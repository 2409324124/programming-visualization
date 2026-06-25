class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __eq__(self, other):
        if not isinstance(other, ListNode):
            return False
        return self.val == other.val and self.next == other.next

    def to_list(self) -> list:
        result = []
        curr = self
        visited = set()
        while curr is not None:
            if id(curr) in visited:
                break  # cycle guard
            visited.add(id(curr))
            result.append(curr.val)
            curr = curr.next
        return result

    def __repr__(self):
        return f"ListNode({self.val})"


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({self.val})"
