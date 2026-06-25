class Solution:
    def __init__(self, trace=None):
        self.trace = trace

    def reverseList(self, head):
        prev = None
        curr = head

        if self.trace:
            self.trace.event(
                event_type="pointer_init",
                message="初始化：prev=None（前一个节点），curr=原来的头节点",
                highlight={"objects": ["ptr:prev", "ptr:curr"]},
                before={"prev": None, "curr": "head"},
                pedagogy={"mental_model": "反转链表就像把一排箭头全部反过来。prev 指向已经反转好的部分，curr 指向正在处理的节点。",
                          "why_now": "从链表头部开始，一个一个反转箭头方向。"}
            )

        while curr is not None:
            next_temp = curr.next
            if self.trace:
                self.trace.event(
                    event_type="save_next",
                    message=f"保存 curr.next 到 next_temp（curr.val={curr.val}，next_temp={next_temp.val if next_temp else 'None'}）",
                    highlight={"objects": ["ptr:curr", "ptr:next_temp"]},
                    before={"curr.val": curr.val, "curr.next": next_temp.val if next_temp else None, "next_temp": next_temp.val if next_temp else None},
                    pedagogy={"why_now": "必须先把 curr.next 存下来，因为下一步要断开这个箭头。不保存的话，后面的链表就丢了。"}
                )

            curr.next = prev
            if self.trace:
                self.trace.event(
                    event_type="link_set",
                    message=f"反转箭头：curr.next 现在指向 prev（curr.val={curr.val} → prev={prev.val if prev else 'None'}）",
                    highlight={"objects": ["ptr:curr", "ptr:prev"], "edge": "curr->prev"},
                    before={"curr.val": curr.val, "prev": prev.val if prev else None},
                    after={"curr.next": prev.val if prev else None},
                    pedagogy={"why_now": "核心动作：把当前节点的 next 指针掉头，从指向下一个变成指向前一个。这就是'反转'。"}
                )

            prev = curr
            curr = next_temp
            if self.trace:
                self.trace.event(
                    event_type="cursor_move",
                    message=f"移动指针：prev 前进到 curr，curr 前进到 next_temp（prev.val={prev.val}）",
                    highlight={"objects": ["ptr:prev", "ptr:curr"]},
                    before={"prev": prev.val, "curr": curr.val if curr else None},
                    after={"prev": prev.val, "curr": curr.val if curr else None},
                    pedagogy={"why_now": "处理完当前节点后，prev 和 curr 都向前移动一步，准备处理下一个节点。"}
                )

        if self.trace:
            self.trace.event(
                event_type="return",
                message=f"循环结束（curr=None），prev 就是新的头节点（prev.val={prev.val if prev else 'None'}）。返回 prev。",
                after={"result": prev.val if prev else None},
                pedagogy={"mental_model": "当 curr 走到 None 时，说明原来的链表末尾已经到了。prev 此时指向的就是反转后的新头部。"}
            )

        return prev
