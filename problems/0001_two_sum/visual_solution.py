class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            if self.trace:
                self.trace.event(
                    event_type="array_read",
                    message=f"读取 nums[{i}] = {num}（索引 {i}，值 {num}）",
                    highlight={"objects": ["arr:nums"], "indices": {"arr:nums": [i]}},
                    before={"i": i, "num": num, "map:seen": dict(seen)},
                    pedagogy={"why_now": "遍历数组，一次只看一个元素。"}
                )
            complement = target - num
            if self.trace:
                self.trace.event(
                    event_type="hash_map_get",
                    message=f"需要补数 {complement}（因为 {num} + {complement} = {target}），检查哈希表...",
                    highlight={"objects": ["map:seen"]},
                    before={"complement": complement, "map:seen": dict(seen)},
                    pedagogy={"why_now": "查哈希表 O(1)，看补数是否存在。"}
                )
            if complement in seen:
                if self.trace:
                    self.trace.event(
                        event_type="answer_found",
                        message=f"找到了！补数 {complement} 在索引 {seen[complement]}，加上当前索引 {i} → [{seen[complement]}, {i}]",
                        highlight={"objects": ["map:seen"], "indices": {}},
                        after={"result": [seen[complement], i]},
                        pedagogy={"mental_model": "哈希表像一本快速查找的字典，key 是见过的值，value 是它的位置。"}
                    )
                return [seen[complement], i]
            seen[num] = i
            if self.trace:
                self.trace.event(
                    event_type="hash_map_put",
                    message=f"把 {num} → 索引 {i} 记录下来，以后可以快速查找",
                    highlight={"objects": ["map:seen"]},
                    before={"map:seen": dict(seen)},
                    after={"map:seen": dict(seen)},
                    pedagogy={"why_now": "当前没找到答案，先记录以便后续查找。"}
                )
        return []
