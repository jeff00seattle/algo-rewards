## Overview
##### Version: 08 May 2018

- [Introduction](#introduction)
- [Example](#example)
- [Usage](#usage)
- [Summary](#summary)

<!-- toc -->

## Introduction

**AlgoRewards** provides a significant performance improvement if your requirements are to perform a quick analysis for traversing a website.

This algorithm traverses the entire tree of API endpoints and returns the sum total rewards.

### Details

+ The input to the algorithm will be a starting url.
+ Making a basic request this endpoint, and all subsequent endpoints will return a JSON response.
  + This JSON response may contain two fields: "children", "reward".
  + (optional) "children": an array of endpoints (str) to be visited.
  + (optional) "reward": an signed float value to be summed.
+ For each page listed in the "children" field, you are to make a request to the given endpoint and
recursively follow down the tree until you have explored all descendants of the starting page.
+ As each page is visited, add up the "reward" fields of the whole tree.
+ This algorithm will return this sum as its result.

| Field     | Type             | Description                                            |
| --------- | ---------------- | ------------------------------------------------------ |
| children  | `[]str`          | 0 or more child URLs, expecting similar JSON responses |
| reward    | `unsigned float` | A value to be summed with the total.                   |

### Warning

It is important to note that **AlgoRewards** does not detect if provide input tree has circular references
and this function will timeout after 60 seconds to avoid endless loops of processing.

## Example

The following bash `curl` call is an example of what the provided start URL should be behaviour:

```bash
curl "[START_URL]" \
  --request GET \
  --verbose \
  --header "Content-Type: application/json" \
  --connect-timeout 60 \
  --location \
  --get \
  --write-out "%{time_total}\n"
```

Calling `[START_URL]` should return the following JSON response:

```json
{
  "children": [
    "[CHILD_URL_B]",
    "[CHILD_URL_C]"
  ],
  "reward": 1
}
```

![Example Node](https://raw.githubusercontent.com/jeff00seattle/images/master/algo/Example_Node_Children_Reward.png "Example Nodes having 'children' and 'reward' fields.")

And the same JSON contents should be available when calling each of the `"children"` URLs.

### AlgoRewards: Expected Result

The following bash `curl` call is an example of what should be response from using `AlgoRewards`:

```bash
curl "https://api.algorithmia.com/v1/algo/jeff00seattle/AlgoRewards/[REDACTED]" \
  --request POST \
  --data "[START_URL]" \
  --header "Content-Type: text/plain" \
  --header "Authorization: Simple [REDACTED]" | jq
```

The field `"result"` will contain the sum of all visited endpoints' "result" values:

```json
{
  "result": 155,
  "metadata": {
    "content_type": "json",
    "duration": 9.849950678999999
  }
}
```

### Applicable Scenarios and Problems

The best purpose of this algorithm is to quickly analysis of all the pages of
your website or API service to determine its ***"total worth"***.

The term ***"total worth"*** is arbitrary to your needs, and what you provide for next "children" to visit,
as long as provided "children" is not circular, then provide a "reward" that has meaning to your needs.

#### Field "reward":
+ The field is assumed to contain an `signed float`, thereby, this algorithm can handle `float` or `int`.
+ Example purposes:
  + How many visits were made to this page?
  + How long did it take for this page to load?
  + How many new comments were added to this page?

#### Field "children":
+ To avoid providing "children" that are not circular, do no provide any URL that could be determined its parent page.
+ The field "children" can contain 0 or more URLs, and there can be duplicates. If this field is empty or not provided, then it is assumed that this is a termination endpoint.


## Usage

### Input

_Describe the input fields for your algorithm. For example:_

| Parameter | Type | Description          |
| --------- | ---- | -------------------- |
| start_url | str  | Description of field |

_What data pre-processing would be great to perform on the input before calling this algorithm?_

### Output

_Describe the output fields for your algorithm. For example:_

| Parameter     | Type  | Description                                 |
| ------------- | ----- | ------------------------------------------- |
| result        | float | sum of the results of all endpoints visited |


#### Example: Traversing Example Tree to gather Rewards

Take the following tree that provides the expected JSON response field response as mentioned earlier from every node:

![Example Tree](https://raw.githubusercontent.com/jeff00seattle/images/master/algo/Example_Tree_Children_Rewards.png "Example Tree with Nodes having 'children' and 'reward' values.")

In more detail, when traversing this tree, the JSON response from each node is as follows:

+ Request Endpoint: `url_endpoint`, `str`
+ Response Endpoints: `array` `url_endpoint` (bag, not unique, expect duplicates): `"children"`
+ Reward: `signed float`
  + Expect negative values: `"reward"`
  + Returned value is consistent with requested `fmt_endpoint` if asked multiple times.
+ Processing Time: `time_total` provided by `curl`
  + Processing time is consistent with requested `fmt_endpoint` if asked multiple times.

This is an example response from each node as far as values from each of the JSON fields, and then covering the response time when calling each of these nodes:


| Request Endpoint  | Processing Time  | Response Endpoints       | Reward | Calls   | Total Rewards | Total Time     |
|-------------------|-----------------:|:------------------------:|-------:|--------:|--------------:|---------------:|
| a                 | 0.197475         | b, c                     | 1      |  1      |  1            | 0.197475       |
| b                 | 6.734861         | d, e                     | 2      |  1      |  2            | 6.734861       |
| c                 | 1.070582         | f, g                     | 3      |  1      |  3            | 1.070582       |
| d                 | 0.394293         | NULL                     | 4      |  1      |  4            | 0.394293       |
| e                 | 0.938208         | NULL                     | 5      |  1      |  5            | 0.938208       |
| f                 | 1.338257         | h                        | 6      |  1      |  6            | 1.338257       |
| g                 | 2.137113         | i (8)                    | 7      |  1      |  7            | 2.137113       |
| h                 | 0.195248         | NULL                     | -1     |  1      |  -1           | 0.195248       |
| i                 | 0.256074         | j (8)                    | 0      |  8      |  0            | 2.048592       |
| j                 | 0.203789         | k (8)                    | 0      |  64     |  0            | 13.042496      |
| k                 | 0.194828         | NULL                     | 0.25   |  512    |  128          | 99.751936      |
|                   |                  |                          |        | **593** |  **155**      | **~128 secs**  |


| Name                                         | Totals                           |
|----------------------------------------------|---------------------------------:|
| Total Number of node calls                   | **593 calls**                    |
| Total Rewards                                | **155 reward points**            |
| Total processing time if called sequencially | **128 seconds**                  |

## Summary

**AlgoRewards** processes the requests asynchronously and in parallel instead of sequencially, thereby a huge time saving:

| Solution Approach                            | Total Processing Time            |
|----------------------------------------------|---------------------------------:|
| Sequencially                                 | **128 seconds**                  |
| **AlgoRewards**                              | **less-than 10 seconds !!!**     |

That is over a ***1000% improvement is processing time!***

