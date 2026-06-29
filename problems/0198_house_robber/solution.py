class Solution:
    def rob(self, nums):
        best_without_prev = 0
        best_with_prev = 0

        for amount in nums:
            current = best_with_prev
            if best_without_prev + amount > current:
                current = best_without_prev + amount
            best_without_prev = best_with_prev
            best_with_prev = current

        return best_with_prev
