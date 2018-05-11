#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
import logging
from logging_fortified import (LoggingFormat, LoggingOutput)

from requests_worker.errors.errors_traceback import (
    print_traceback
)
import queue
import datetime as dt

from concurrent import futures
from urllib.parse import unquote as urldecode

from logging_fortified import (get_logger)

from requests_fortified.errors import (
    get_exception_message,
    error_name,
)
from requests_fortified.support import (
    base_class_name,
    HEADER_CONTENT_TYPE_APP_JSON,)

from requests_fortified import RequestsFortifiedDownload

from requests_worker.support.utils import parse_config_logger

SECONDS_FOR_60_MINUTES = 3600

class WorkRequest(object):
    def __init__(self, request_url):
        self.__request_url = request_url

    @property
    def request_url(self):
        return self.__request_url

    @request_url.setter
    def request_url(self, value):
        self.__request_url = value

class WorkResponse(WorkRequest):
    def __init__(self, request_url, children, reward):
        self.__children = children
        self.__reward = reward
        self.request_url = request_url

    @property
    def children(self):
        return self.__children

    @children.setter
    def children(self, value):
        self.__children = value

    @property
    def reward(self):
        return float(self.__reward)

    @reward.setter
    def result(self, value):
        self.__reward += float(value)


class AlgoRewards(object):
    _WORKER_NAME = "Algo Rewards"
    _WORKER_VERSION = "0.0.1"

    _MAX_WORKERS = 10

    @property
    def rewards_url(self):
        return self.__rewards_url

    @rewards_url.setter
    def rewards_url(self, value):
        self.__rewards_url = value

    #
    # Initialize
    #
    def __init__(self, rewards_url, config_logger=None):
        """Initialize
        """
        assert rewards_url

        self.rewards_url = rewards_url

        if config_logger:
            logger_level, logger_format, logger_output = parse_config_logger(config_logger=config_logger)
        else:
            logger_level, logger_format, logger_output = (logging.WARNING, LoggingFormat.JSON, LoggingOutput.STDOUT_COLOR)

        self.logger_level = logger_level
        self.logger_format = logger_format
        self.logger_output = logger_output

        self.run_start_time = dt.datetime.now()
        self.run_timeout_msec = SECONDS_FOR_60_MINUTES * 1000

        self.logger = get_logger(
            logger_name=self._WORKER_NAME,
            logger_version=self._WORKER_VERSION,
            logger_format=self.logger_format,
            logger_level=self.logger_level,
            logger_output=self.logger_output
        )

    __worker_queue = queue.Queue()
    __total_reward = 0.0
    @property
    def total_reward(self):
        return float(self.__total_reward)
    def total_reward_increment(self, reward):
        self.__total_reward += float(reward)

    __total_calls = 0
    @property
    def total_calls(self):
        return self.__total_calls
    def total_calls_increment(self, calls):
        self.__total_calls += calls


    __base_request = None
    @property
    def base_request(self):
        if self.__base_request is None:
            self.__base_request = RequestsFortifiedDownload(
                logger_format=self.logger_format,
                logger_level=self.logger_level,
                logger_output=self.logger_output
            )

        return self.__base_request

    #
    # Worker:
    #
    def work(
        self
    ):
        try:
            num_worker_threads = self._MAX_WORKERS
            self.__worker_queue.put(WorkRequest(request_url=self.rewards_url))

            with futures.ThreadPoolExecutor(max_workers=num_worker_threads) as executor:
                # executor.submit schedule self.process_account to be executed
                # for each account and returns a future representing this
                # pending operation.
                threads = []
                while not self.__worker_queue.empty():
                    wreq = self.__worker_queue.get()
                    self.logger.debug(
                        f"request_url: {wreq.request_url}"
                    )
                    future = executor.submit(self.work_process, wreq)
                    threads.append(future)

                    for future in futures.as_completed(threads):
                        future.result()

                        if not self.__worker_queue.empty():
                            wreq = self.__worker_queue.get()
                            self.logger.debug(
                                f"request_url: {wreq.request_url}"
                            )
                            future = executor.submit(self.work_process, wreq)
                            threads.append(future)


        except Exception as ex:
            self.logger.error(
                'Worker: Failed: Unexpected Error',
                extra={'error_exception': base_class_name(ex),
                       'error_details': get_exception_message(ex)})
            raise

        self.logger.debug(f"TOTAL REWARD: {self.total_reward}")

        return self.total_reward

    def work_process(self, wreq):
        assert wreq
        assert wreq.request_url

        self.total_calls_increment(1)
        response = self.worker_request(
            request_method="GET",
            request_url=wreq.request_url,
            request_headers=HEADER_CONTENT_TYPE_APP_JSON,
            request_label=f"request_url '{wreq.request_url}': Request"
        )

        status_code = response.status_code

        if status_code != 200:
            raise Exception(error_name(status_code))

        json_response = response.json()
        self.logger.debug(f"request_url: {wreq.request_url}",extra=json_response)

        wresp = WorkResponse(
            request_url=wreq.request_url,
            children=json_response.get("children", []),
            reward=float(json_response.get("reward", 0.0))
        )

        self.total_reward_increment(wresp.reward)
        wq = queue.Queue()
        for request_url in wresp.children:
            self.__worker_queue.put(WorkRequest(request_url=request_url))

        return wq

    def worker_request(
        self,
        request_method,
        request_url,
        request_params=None,
        request_data=None,
        request_retry=None,
        request_headers=None,
        request_label=None
    ):
        """
        :param request_method:
        :param request_url:
        :param request_params:
        :param request_data:
        :param request_retry:
        :param request_headers:
        :param request_label:
        :return:
        """
        request_data_decoded = None
        if request_data:
            request_data_decoded = urldecode(request_data)

        self.logger.debug(
            "Request",
            extra={
                'request_method': request_method,
                'request_url': request_url,
                'request_params': request_params,
                'request_data_decoded': request_data_decoded})

        response = None
        delay_secs = 2
        tries = 0

        while True:
            tries += 1
            if tries > 1:
                _request_label = f'{request_label}: Attempt {tries}'
            else:
                _request_label = request_label

            try:
                response = self.base_request.request(
                    request_method=request_method,
                    request_url=request_url,
                    request_params=request_params,
                    request_data=request_data,
                    request_retry=request_retry,
                    request_retry_excps_func=None,
                    request_headers=request_headers,
                    request_label=_request_label
                )
            except Exception as ex:
                print_traceback(ex)
                raise

            return response


if __name__ == '__main__':
    worker_class = AlgoRewards(rewards_url="http://algo.work/interview/a")
    total_rewards = worker_class.work()
    print(f"total_rewards: {total_rewards}")
