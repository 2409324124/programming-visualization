class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def rob(self, nums):
        if not nums:
            if self.trace:
                self.trace.event(
                    event_type="dp_init",
                    message="没有房屋，最大金额是 0。",
                    before={"nums": nums},
                    pedagogy={
                        "mental_model": "DP 表格里每一格表示'看到这间房为止，最多能拿多少钱'。没有房屋时表格为空。"
                    },
                )
                self.trace.event(
                    event_type="return",
                    message="返回 0",
                    after={"result": 0},
                )
            return 0

        dp = [0] * len(nums)

        if self.trace:
            self.trace.event(
                event_type="dp_init",
                message=f"创建 DP 表格：共有 {len(nums)} 间房。dp[i] 表示看完第 i 间房后，最多能拿多少钱。",
                highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [0], "dp:table": [0]}},
                before={"nums": nums},
                pedagogy={
                    "mental_model": "每到一间房，都只做一个选择：跳过它，或者偷它。因为相邻房子不能同时选，偷当前房时只能接在 dp[i-2] 后面。",
                    "why_now": "先把输入排成一排，再从左到右填 DP 表格。",
                },
            )

        for i, amount in enumerate(nums):
            if i == 0:
                skip_current = 0
                take_current = amount
                if self.trace:
                    self.trace.event(
                        event_type="choose_transition",
                        message=f"第 0 间房没有左邻选择冲突：偷它可以拿 {take_current}，跳过是 {skip_current}。",
                        highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [0], "dp:table": [0]}},
                        before={"i": i, "nums[i]": amount, "skip_current": skip_current, "take_current": take_current},
                        pedagogy={"why_now": "第一间房之前没有历史选择，直接比较偷和不偷。"},
                    )
                dp[i] = amount
            elif i == 1:
                skip_current = dp[i - 1]
                take_current = amount
                if self.trace:
                    self.trace.event(
                        event_type="dp_read",
                        message=f"读取 dp[0]={dp[0]}。第 1 间房如果要偷，就不能同时偷第 0 间。",
                        highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [i], "dp:table": [0, 1]}},
                        before={"i": i, "nums[i]": amount, "dp[i-1]": dp[i - 1]},
                        pedagogy={"why_now": "两间相邻房只能选一边，所以第 1 格只需要和第 0 格比较。"},
                    )
                    self.trace.event(
                        event_type="choose_transition",
                        message=f"比较：跳过当前房得到 {skip_current}；偷当前房得到 {take_current}。",
                        highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [i], "dp:table": [0, 1]}},
                        before={"skip_current": skip_current, "take_current": take_current},
                        pedagogy={"why_now": "DP 的选择不是'看到大数字就拿'，而是比较两条合法路线的总金额。"},
                    )
                dp[i] = skip_current if skip_current >= take_current else take_current
            else:
                skip_current = dp[i - 1]
                take_current = dp[i - 2] + amount
                if self.trace:
                    self.trace.event(
                        event_type="dp_read",
                        message=f"读取 dp[{i-1}]={dp[i-1]}（跳过当前房）和 dp[{i-2}]={dp[i-2]}（偷当前房前的安全位置）。",
                        highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [i], "dp:table": [i - 2, i - 1, i]}},
                        before={"i": i, "nums[i]": amount, "dp[i-2]": dp[i - 2], "dp[i-1]": dp[i - 1]},
                        pedagogy={"why_now": "偷第 i 间房时，第 i-1 间必须跳过，所以只能加上 dp[i-2]。"},
                    )
                    self.trace.event(
                        event_type="choose_transition",
                        message=f"比较：跳过当前房得到 {skip_current}；偷当前房得到 dp[{i-2}] + nums[{i}] = {dp[i-2]} + {amount} = {take_current}。",
                        highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [i], "dp:table": [i - 2, i - 1, i]}},
                        before={"skip_current": skip_current, "take_current": take_current},
                        pedagogy={"why_now": "每一格都保存到当前位置的最好结果，不需要记住具体偷了哪些房。"},
                    )
                dp[i] = skip_current if skip_current >= take_current else take_current

            if self.trace:
                choice = "跳过当前房" if dp[i] == skip_current else "偷当前房"
                self.trace.event(
                    event_type="dp_write",
                    message=f"写入 dp[{i}] = {dp[i]}（{choice}）。",
                    highlight={"objects": ["arr:nums", "dp:table"], "indices": {"arr:nums": [i], "dp:table": [i]}},
                    before={"dp_idx": i},
                    after={"dp_idx": i, "dp_val": dp[i], "choice": choice},
                    pedagogy={"why_now": "把当前最优结果记下来，后面的房屋会继续引用这个结果。"},
                )

        if self.trace:
            self.trace.event(
                event_type="return",
                message=f"DP 表格填完，最后一格 dp[{len(nums)-1}] = {dp[-1]}，这就是最大金额。",
                after={"result": dp[-1]},
                pedagogy={"mental_model": "最后一格表示'看完所有房屋后，能拿到的最大金额'。"},
            )

        return dp[-1]
