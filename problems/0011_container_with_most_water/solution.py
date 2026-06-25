class Solution:
    def maxArea(self, height):
        left = 0
        right = len(height) - 1
        best = 0

        while left < right:
            h = height[left] if height[left] < height[right] else height[right]
            w = right - left
            area = h * w
            if area > best:
                best = area

            if height[left] < height[right]:
                left += 1
            else:
                right -= 1

        return best
