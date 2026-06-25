class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def climbStairs(self, n):
        if n <= 2:
            if self.trace:
                self.trace.event(
                    event_type="dp_init",
                    message=f"n={n} ≤ 2，直接返回 n。dp[0]=1, dp[1]=1（基础情况）",
                    before={"n": n},
                    pedagogy={"mental_model": "DP 表格中每个格子 dp[i] 表示'走到第 i 级台阶有几种方法'。dp[0]=1（地面），dp[1]=1（走一步）。"}
                )
                self.trace.event(
                    event_type="return",
                    message=f"返回 {n}",
                    after={"result": n},
                )
            return n

        dp = [0] * (n + 1)
        dp[0] = 1
        dp[1] = 1

        if self.trace:
            self.trace.event(
                event_type="dp_init",
                message=f"创建 DP 表格：dp[0] 到 dp[{n}]，共 {n+1} 格。dp[0]=1（地面，0 级台阶有 1 种走法：不走），dp[1]=1（走 1 步到第 1 级）。",
                highlight={"objects": ["dp:table"], "indices": {"dp:table": [0, 1]}},
                before={"n": n, "dp[0]": 1, "dp[1]": 1},
                pedagogy={
                    "mental_model": "把 DP 表格想象成一排格子，每个格子里写着'走到这一级台阶有几种方法'。",
                    "why_now": "基础情况直接写好：0 级有 1 种方法（不动），1 级有 1 种方法（走 1 步）。"
                }
            )

        for i in range(2, n + 1):
            if self.trace:
                self.trace.event(
                    event_type="dp_read",
                    message=f"读取 dp[{i-2}]={dp[i-2]}（2 步前）和 dp[{i-1}]={dp[i-1]}（1 步前）",
                    highlight={"objects": ["dp:table"], "indices": {"dp:table": [i-2, i-1]}},
                    before={"i": i, "dp[i-2]": dp[i-2], "dp[i-1]": dp[i-1]},
                    pedagogy={"why_now": "你要走到第 i 级，要么从 i-1 走 1 步上来，要么从 i-2 走 2 步上来。所以需要这两格的数据。"}
                )

            dp[i] = dp[i - 1] + dp[i - 2]

            if self.trace:
                self.trace.event(
                    event_type="transition_considered",
                    message=f"计算 dp[{i}] = dp[{i-1}] + dp[{i-2}] = {dp[i-1]} + {dp[i-2]} = {dp[i]}",
                    highlight={"objects": ["dp:table"], "indices": {"dp:table": [i-2, i-1, i]}},
                    before={"dp[i-2]": dp[i-2], "dp[i-1]": dp[i-1], "dp[i]": dp[i]},
                    after={"dp[i]": dp[i]},
                    pedagogy={"why_now": f"到第 {i} 级的方法 = 到第 {i-1} 级的方法（再走 1 步）+ 到第 {i-2} 级的方法（再走 2 步）。"}
                )

            if self.trace:
                self.trace.event(
                    event_type="dp_write",
                    message=f"写入 dp[{i}] = {dp[i]}",
                    highlight={"objects": ["dp:table"], "indices": {"dp:table": [i]}},
                    before={"dp[i]": dp[i]},
                    after={"dp[i]": dp[i]},
                    pedagogy={"why_now": "把计算结果记下来。后面算 dp[i+1] 和 dp[i+2] 时会用到这个值。"}
                )

        if self.trace:
            self.trace.event(
                event_type="return",
                message=f"DP 表格填充完毕。最终答案 dp[{n}] = {dp[n]}",
                after={"result": dp[n]},
                pedagogy={"mental_model": "整个表格填满后，最后一个格子就是答案。"}
            )

        return dp[n]
