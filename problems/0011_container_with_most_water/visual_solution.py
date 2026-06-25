class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def maxArea(self, height):
        left = 0
        right = len(height) - 1
        best = 0

        if self.trace:
            self.trace.event(
                event_type="pointer_init",
                message=f"初始化指针：left=0（高度={height[0]}），right={len(height)-1}（高度={height[-1]}）",
                highlight={"objects": ["ptr:left", "ptr:right"]},
                before={"left": 0, "right": len(height) - 1, "height": height},
                pedagogy={"why_now": "双指针从数组两端开始，宽度最大时先计算面积，然后逐步缩小。",
                          "mental_model": "想象两块板子之间的距离就是容器的宽度，短板决定了能装多少水。"}
            )

        while left < right:
            h = height[left] if height[left] < height[right] else height[right]
            w = right - left
            area = h * w

            if self.trace:
                self.trace.event(
                    event_type="area_compute",
                    message=f"当前 left={left}（高度={height[left]}），right={right}（高度={height[right]}），宽度={w}，较短高度={h}，面积={area}",
                    highlight={"objects": ["ptr:left", "ptr:right"], "indices": {"arr:height": [left, right]}},
                    before={"left": left, "right": right, "left_h": height[left], "right_h": height[right], "width": w, "height_min": h, "area": area, "best": best},
                    pedagogy={"why_now": f"面积 = 宽度({w}) × 较短高度({h})。任何向内移动都会减少宽度，所以只有移动短板才有可能让高度变大、面积更大。"}
                )

            if area > best:
                best = area
                if self.trace:
                    self.trace.event(
                        event_type="best_update",
                        message=f"更新最大面积！新的最佳面积 = {best}",
                        highlight={"objects": ["ptr:left", "ptr:right"]},
                        after={"best": best},
                        pedagogy={"why_now": "当前的容器比之前找到的都要大，记录下来。"}
                    )

            if height[left] < height[right]:
                if self.trace:
                    self.trace.event(
                        event_type="comparison_reason",
                        message=f"左侧高度({height[left]}) < 右侧高度({height[right]})，移动左指针（因为短板在左边，移动它才有可能让高度增加）",
                        highlight={"objects": ["ptr:left"]},
                        before={"left": left, "left_h": height[left], "right_h": height[right]},
                        pedagogy={"why_now": "为什么移动更短的一侧？因为面积取决于短板的高度。如果移动长板，宽度减小而短板高度不变，面积只可能更小。移动短板才有机会遇到更高的板。"}
                    )
                left += 1
                if self.trace:
                    self.trace.event(
                        event_type="pointer_move",
                        message=f"左指针右移 → left={left}",
                        highlight={"objects": ["ptr:left"]},
                        after={"left": left, "right": right}
                    )
            else:
                if self.trace:
                    self.trace.event(
                        event_type="comparison_reason",
                        message=f"右侧高度({height[right]}) <= 左侧高度({height[left]})，移动右指针（因为短板在右边，移动它才有可能让高度增加）",
                        highlight={"objects": ["ptr:right"]},
                        before={"right": right, "left_h": height[left], "right_h": height[right]},
                        pedagogy={"why_now": "同理，面积由短板决定。移动长板不会增加面积上限，所以向内移动短板。"}
                    )
                right -= 1
                if self.trace:
                    self.trace.event(
                        event_type="pointer_move",
                        message=f"右指针左移 → right={right}",
                        highlight={"objects": ["ptr:right"]},
                        after={"left": left, "right": right}
                    )

        if self.trace:
            self.trace.event(
                event_type="return",
                message=f"双指针相遇，结束。最大面积 = {best}",
                after={"result": best},
                pedagogy={"mental_model": "从两端向中间扫描，每次只移动短板，必然不会错过最大面积。"}
            )

        return best
