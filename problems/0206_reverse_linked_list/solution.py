class Solution:
    def reverseList(self, head):
        prev = None
        curr = head
        while curr is not None:
            next_temp = curr.next
            curr.next = prev
            prev = curr
            curr = next_temp
        return prev
