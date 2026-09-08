#!/usr/bin/env python3
"""Shape D programmatic builder for gen_topup4 part 1 (algorithms).

Each topic yields 3 problem variants with prose explanation and code body.
Code must parse and include ```python``` fences (Shape D validator).
Index range: batch_g1000..batch_g1099.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _topic(name, problems, prose, code):
    return (name, problems, prose, code)


# Group 1: classic array/string problems ----------------------------------------
def _two_sum(): return _topic(
    "qx2_two_sum_v2",
    ["Compute all unique pairs in [2, 7, 11, 15] summing to 9.",
     "Compute all pairs in [3, 2, 4] summing to 6.",
     "Compute all pairs in [3, 3] summing to 6."],
    "Use a hashmap from value to list of indices. Walk the array; for each element, look up `target - x`. If found, record the pair. O(n) per pass.",
    ["def two_sum_all(nums, target):",
     "    out = []",
     "    seen = {}",
     "    for i, n in enumerate(nums):",
     "        complement = target - n",
     "        if complement in seen:",
     "            for j in seen[complement]:",
     "                out.append((j, i))",
     "        seen.setdefault(n, []).append(i)",
     "    return out"])


def _max_subarray(): return _topic(
    "qx2_max_subarray_v2",
    ["Find the contiguous subarray with maximum sum in [-2, 1, -3, 4, -1, 2, 1, -5, 4].",
     "Find the max subarray sum in [1].",
     "Find the max subarray sum in [-3, -2, -1]."],
    "Kadane's algorithm: keep a running sum, reset to 0 if it goes negative. The max over all running sums is the answer. O(n).",
    ["def max_subarray_v2(arr):",
     "    cur = 0",
     "    best = float('-inf')",
     "    for v in arr:",
     "        cur = max(v, cur + v)",
     "        best = max(best, cur)",
     "    return best"])


def _product_except_self(): return _topic(
    "qx2_product_except_self_v2",
    ["Compute product of all-but-self in [1, 2, 3, 4].",
     "Compute in [0, 1, 2, 3].",
     "Compute in [2, 3]."],
    "Compute prefix and suffix products in two passes. Output[i] = prefix[i] * suffix[i]. O(n) time and O(1) extra.",
    ["def product_except_self_v2(arr):",
     "    n = len(nums)",
     "    out = [1] * n",
     "    p = 1",
     "    for i in range(n):",
     "        out[i] = p",
     "        p *= nums[i]",
     "    s = 1",
     "    for i in range(n - 1, -1, -1):",
     "        out[i] *= s",
     "        s *= nums[i]",
     "    return out"])


def _contains_duplicate(): return _topic(
    "qx2_contains_duplicate_v2",
    ["Check [1, 2, 3, 1] for duplicates.",
     "Check [1, 2, 3, 4].",
     "Check [] for duplicates."],
    "Insert each element into a set; if it's already there, we have a duplicate. O(n) time, O(n) space.",
    ["def contains_duplicate_v2(arr):",
     "    seen = set()",
     "    for x in xs:",
     "        if x in seen:",
     "            return True",
     "        seen.add(x)",
     "    return False"])


def _best_time_stock(): return _topic(
    "qx2_best_time_stock_v2",
    ["Max profit with single buy/sell in [7, 1, 5, 3, 6, 4].",
     "Max profit with single buy/sell in [7, 6, 4, 3, 1].",
     "Max profit with single buy/sell in [1, 2]."],
    "Track the minimum price seen so far; for each day, compute profit if sold today. Take the max. O(n).",
    ["def max_profit(prices):",
     "    if not prices:",
     "        return 0",
     "    min_p = prices[0]",
     "    best = 0",
     "    for p in prices[1:]:",
     "        best = max(best, p - min_p)",
     "        min_p = min(min_p, p)",
     "    return best"])


def _climb_stairs(): return _topic(
    "qx2_climb_stairs_v2",
    ["Count distinct ways to climb n=5 stairs with 1 or 2 step strides.",
     "Count ways for n=10.",
     "Count ways for n=0 (base case)."],
    "Let f(n) be the count. Then f(n) = f(n-1) + f(n-2). Fibonacci. Base: f(0)=1, f(1)=1.",
    ["def climb_stairs_v2(n):",
     "    if n < 0:",
     "        raise ValueError('n must be >= 0')",
     "    if n <= 1:",
     "        return 1",
     "    a, b = 1, 1",
     "    for _ in range(2, n + 1):",
     "        a, b = b, a + b",
     "    return b"])


def _valid_parens(): return _topic(
    "qx2_valid_parens_v2",
    ["Check '()[]{}' for valid bracketing.",
     "Check '([)]'.",
     "Check '{[()]}'."],
    "Use a stack: push opening brackets; on closing, check top matches. At end, stack must be empty.",
    ["def is_valid_v2(s):",
     "    pairs = {')': '(', ']': '[', '}': '{'}",
     "    stack = []",
     "    for ch in s:",
     "        if ch in '([{':",
     "            stack.append(ch)",
     "        elif ch in ')]}':",
     "            if not stack or stack[-1] != pairs[ch]:",
     "                return False",
     "            stack.pop()",
     "    return not stack"])


def _group_anagrams(): return _topic(
    "qx2_group_anagrams_v2",
    ["Group ['eat','tea','tan','ate','nat','bat'] by anagram class.",
     "Group [''] by anagram.",
     "Group ['a'] by anagram."],
    "Sort each string and use as the group key. Words in the same anagram class have the same sorted form.",
    ["from collections import defaultdict",
     "def group_anagrams(words):",
     "    groups = defaultdict(list)",
     "    for w in words:",
     "        groups[''.join(sorted(w))].append(w)",
     "    return list(groups.values())"])


def _longest_substring_no_repeat(): return _topic(
    "qx2_longest_no_repeat_v2",
    ["Find the longest substring of 'abcabcbb' with no repeats.",
     "Find it in 'bbbbb'.",
     "Find it in 'pwwkew'."],
    "Sliding window with a set of seen chars. Expand right; if char is in set, shrink left until it's not. Track max window size.",
    ["def longest_no_repeat(s):",
     "    seen = set()",
     "    left = 0",
     "    best = 0",
     "    for right, ch in enumerate(s):",
     "        while ch in seen:",
     "            seen.remove(s[left])",
     "            left += 1",
     "        seen.add(ch)",
     "        best = max(best, right - left + 1)",
     "    return best"])


def _top_k_frequent(): return _topic(
    "qx2_top_k_frequent_v2",
    ["Find the k=2 most frequent elements in [1, 1, 1, 2, 2, 3].",
     "Find top k=1 in [1].",
     "Find top k=1 in [1, 2]."],
    "Counter for frequencies; use heapq.nlargest for k largest. O(n log k) time.",
    ["import heapq",
     "from collections import Counter",
     "",
     "def top_k_frequent(xs, k):",
     "    counts = Counter(xs)",
     "    return [x for x, _ in counts.most_common(k)]"])


def _reverse_linked_list(): return _topic(
    "qx2_reverse_list_v2",
    ["Reverse [1, 2, 3, 4, 5] as a singly linked list.",
     "Reverse [1].",
     "Reverse []."],
    "Iteratively flip next pointers. Three pointers: prev, curr, next.",
    ["def reverse_list(head):",
     "    prev = None",
     "    curr = head",
     "    while curr:",
     "        nxt = curr.next",
     "        curr.next = prev",
     "        prev = curr",
     "        curr = nxt",
     "    return prev"])


def _merge_sorted_arrays(): return _topic(
    "qx2_merge_sorted_v2",
    ["Merge [1, 2, 4] and [1, 3, 4].",
     "Merge [] and [1].",
     "Merge [0] and [0]."],
    "Two pointers. Pick the smaller head each step; advance that pointer.",
    ["def merge_sorted(a, b):",
     "    out = []",
     "    i = j = 0",
     "    while i < len(a) and j < len(b):",
     "        if a[i] <= b[j]:",
     "            out.append(a[i])",
     "            i += 1",
     "        else:",
     "            out.append(b[j])",
     "            j += 1",
     "    out.extend(a[i:])",
     "    out.extend(b[j:])",
     "    return out"])


def _binary_search(): return _topic(
    "qx2_binary_search_v2",
    ["Find 4 in [-1, 0, 3, 5, 9, 12]; should return 4.",
     "Find 2 in [-1, 0, 3, 5, 9, 12]; should return -1.",
     "Find 5 in [5]; should return 0."],
    "Two pointers, mid = (lo+hi)//2. If arr[mid] == target, return mid. If < target, search right half; else left.",
    ["def binary_search(arr, target):",
     "    lo, hi = 0, len(arr) - 1",
     "    while lo <= hi:",
     "        mid = (lo + hi) // 2",
     "        if arr[mid] == target:",
     "            return mid",
     "        if arr[mid] < target:",
     "            lo = mid + 1",
     "        else:",
     "            hi = mid - 1",
     "    return -1"])


def _rotate_array(): return _topic(
    "qx2_rotate_array_v2",
    ["Rotate [1, 2, 3, 4, 5, 6, 7] right by 3 steps -> [5, 6, 7, 1, 2, 3, 4].",
     "Rotate [1] right by 0.",
     "Rotate [1, 2] right by 1."],
    "Triple reverse: reverse all, reverse first k, reverse last n-k. O(n) time, O(1) space.",
    ["def rotate(nums, k):",
     "    k = k % len(nums)",
     "    nums.reverse()",
     "    nums[:k] = reversed(nums[:k])",
     "    nums[k:] = reversed(nums[k:])",
     "    return nums"])


def _3sum(): return _topic(
    "qx2_3sum_v2",
    ["Find all unique triplets in [-1, 0, 1, 2, -1, -4] summing to 0.",
     "Find all in [0, 1, 1].",
     "Find all in [0, 0, 0]."],
    "Sort; fix one element, two-pointer the rest. Skip duplicates carefully to get unique triplets.",
    ["def three_sum(nums):",
     "    nums.sort()",
     "    out = []",
     "    for i in range(len(nums) - 2):",
     "        if i > 0 and nums[i] == nums[i-1]:",
     "            continue",
     "        lo, hi = i + 1, len(nums) - 1",
     "        while lo < hi:",
     "            s = nums[i] + nums[lo] + nums[hi]",
     "            if s == 0:",
     "                out.append((nums[i], nums[lo], nums[hi]))",
     "                while lo < hi and nums[lo] == nums[lo+1]:",
     "                    lo += 1",
     "                while lo < hi and nums[hi] == nums[hi-1]:",
     "                    hi -= 1",
     "                lo += 1; hi -= 1",
     "            elif s < 0:",
     "                lo += 1",
     "            else:",
     "                hi -= 1",
     "    return out"])


def _container_most_water(): return _topic(
    "qx2_container_water_v2",
    ["Max water in [1, 8, 6, 2, 5, 4, 8, 3, 7].",
     "Max water in [1, 1].",
     "Max water in [4, 3, 2, 1, 4]."],
    "Two pointers at both ends; move the shorter side inward (since the wider one is the limiting height).",
    ["def max_area(height):",
     "    lo, hi = 0, len(height) - 1",
     "    best = 0",
     "    while lo < hi:",
     "        best = max(best, min(height[lo], height[hi]) * (hi - lo))",
     "        if height[lo] < height[hi]:",
     "            lo += 1",
     "        else:",
     "            hi -= 1",
     "    return best"])


def _trapping_rain_water(): return _topic(
    "qx2_trap_rain_v2",
    ["Trap rain in [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]; answer 6.",
     "Trap rain in [4, 2, 0, 3, 2, 5].",
     "Trap rain in [1, 0, 1]."],
    "Two-pointer: track max-left and max-right; move the smaller side in, accumulating trapped water.",
    ["def trap(height):",
     "    if not height:",
     "        return 0",
     "    lo, hi = 0, len(height) - 1",
     "    left_max, right_max = height[lo], height[hi]",
     "    water = 0",
     "    while lo < hi:",
     "        if left_max < right_max:",
     "            lo += 1",
     "            left_max = max(left_max, height[lo])",
     "            water += left_max - height[lo]",
     "        else:",
     "            hi -= 1",
     "            right_max = max(right_max, height[hi])",
     "            water += right_max - height[hi]",
     "    return water"])


def _min_window_substring(): return _topic(
    "qx2_min_window_v2",
    ["Find the minimum window in 'ADOBECODEBANC' containing 'ABC'.",
     "Find it in 'a' containing 'a'.",
     "Find it in 'a' containing 'aa'."],
    "Sliding window with two hashmap counts: one for target, one for current window. Expand right, contract left when window is valid.",
    ["from collections import Counter",
     "",
     "def min_window(s, t):",
     "    if not s or not t:",
     "        return ''",
     "    need = Counter(t)",
     "    missing = len(t)",
     "    left = start = end = 0",
     "    for right, ch in enumerate(s, 1):",
     "        if need[ch] > 0:",
     "            missing -= 1",
     "        need[ch] -= 1",
     "        if missing == 0:",
     "            while need[s[left]] < 0:",
     "                need[s[left]] += 1",
     "                left += 1",
     "            if not end or right - left <= end - start:",
     "                start, end = left, right",
     "            need[s[left]] += 1",
     "            missing += 1",
     "            left += 1",
     "    return s[start:end]"])


def _longest_palindromic_substring(): return _topic(
    "qx2_longest_pal_v2",
    ["Find longest palindromic substring in 'babad'; 'bab' or 'aba'.",
     "Find it in 'cbbd'; 'bb'.",
     "Find it in 'a'; 'a'."],
    "Expand-around-center: for each center, expand outward while palindrome holds. O(n^2) total.",
    ["def longest_palindrome(s):",
     "    if not s:",
     "        return ''",
     "    start, end = 0, 0",
     "    for i in range(len(s)):",
     "        l1, r1 = expand(s, i, i)",
     "        l2, r2 = expand(s, i, i + 1)",
     "        for l, r in ((l1, r1), (l2, r2)):",
     "            if r - l > end - start:",
     "                start, end = l, r",
     "    return s[start:end + 1]",
     "",
     "def expand(s, lo, hi):",
     "    while lo >= 0 and hi < len(s) and s[lo] == s[hi]:",
     "        lo -= 1",
     "        hi += 1",
     "    return lo + 1, hi - 1"])


def _palindromic_substrings_count(): return _topic(
    "qx2_pal_count_v2",
    ["Count palindromic substrings in 'abc'; answer 3.",
     "Count in 'aaa'; answer 6.",
     "Count in 'abba'; answer 6."],
    "Expand around each center; count each successful expansion as one palindromic substring.",
    ["def count_palindromes(s):",
     "    count = 0",
     "    for i in range(len(s)):",
     "        for lo, hi in ((i, i), (i, i + 1)):",
     "            while lo >= 0 and hi < len(s) and s[lo] == s[hi]:",
     "                count += 1",
     "                lo -= 1",
     "                hi += 1",
     "    return count"])


def _decode_ways(): return _topic(
    "qx2_decode_ways_v2",
    ["Count decodings of '226'; answer 3.",
     "Count of '12'; answer 2.",
     "Count of '0'; answer 0."],
    "DP: dp[i] = number of ways to decode s[:i]. Recurrence handles 1-9 (single) and 10-26 (pair). Skip '0's.",
    ["def num_decodings(s):",
     "    if not s or s[0] == '0':",
     "        return 0",
     "    dp = [0] * (len(s) + 1)",
     "    dp[0] = dp[1] = 1",
     "    for i in range(2, len(s) + 1):",
     "        if s[i-1] != '0':",
     "            dp[i] += dp[i-1]",
     "        if 10 <= int(s[i-2:i]) <= 26:",
     "            dp[i] += dp[i-2]",
     "    return dp[-1]"])


def _word_break(): return _topic(
    "qx2_word_break_v2",
    ["Check if 'leetcode' can be segmented using {'leet','code'}.",
     "Check 'applepenapple' using {'apple','pen'}.",
     "Check 'catsandog' using {'cats','dog','sand','and','cat'}."],
    "DP: dp[i] = True if s[:i] can be segmented. For each i, try all word lengths.",
    ["def word_break(s, word_dict):",
     "    n = len(s)",
     "    dp = [False] * (n + 1)",
     "    dp[0] = True",
     "    for i in range(1, n + 1):",
     "        for w in word_dict:",
     "            if dp[i - len(w)] and s[i - len(w):i] == w:",
     "                dp[i] = True",
     "                break",
     "    return dp[n]"])


def _coin_change(): return _topic(
    "qx2_coin_change_v2",
    ["Min coins to make 11 from [1, 2, 5]; answer 3.",
     "Min coins to make 3 from [2]; answer -1.",
     "Min coins to make 0 from [1]; answer 0."],
    "DP: dp[amt] = min coins. Initialize dp[0] = 0; for each coin, update dp[amt] for amt >= coin.",
    ["def coin_change(coins, amount):",
     "    dp = [float('inf')] * (amount + 1)",
     "    dp[0] = 0",
     "    for c in coins:",
     "        for amt in range(c, amount + 1):",
     "            dp[amt] = min(dp[amt], dp[amt - c] + 1)",
     "    return dp[amount] if dp[amount] != float('inf') else -1"])


def _house_robber(): return _topic(
    "qx2_house_robber_v2",
    ["Max loot from [1, 2, 3, 1]; answer 4.",
     "From [2, 7, 9, 3, 1]; answer 12.",
     "From [2, 1, 1, 2]; answer 4."],
    "DP: dp[i] = max(dp[i-1], dp[i-2] + nums[i]). At each house, choose to rob or skip.",
    ["def rob(nums):",
     "    if not nums:",
     "        return 0",
     "    prev, curr = 0, 0",
     "    for n in nums:",
     "        prev, curr = curr, max(curr, prev + n)",
     "    return curr"])


def _subset_sum(): return _topic(
    "qx2_subset_sum_v2",
    ["Check if subset of [3, 34, 4, 12, 5, 2] sums to 9; True.",
     "Check subset of [3, 34, 4, 12, 5, 2] sums to 30; False.",
     "Check subset of [1] sums to 1; True."],
    "DP on sums: dp[s] = True if some subset sums to s. For each num, update dp from high to low to avoid reuse.",
    ["def subset_sum(nums, target):",
     "    dp = [False] * (target + 1)",
     "    dp[0] = True",
     "    for n in nums:",
     "        for s in range(target, n - 1, -1):",
     "            dp[s] = dp[s] or dp[s - n]",
     "    return dp[target]"])


def _bfs_shortest_path(): return _topic(
    "qx2_bfs_shortest_v2",
    ["Shortest path from A to F in the graph A->B->C->F, A->D->F.",
     "Shortest path from 1 to 4 in {1:[2,3], 2:[4], 3:[4]}.",
     "Shortest path in a 3x3 grid from (0,0) to (2,2) (4-directional moves)."],
    "BFS from source. Track visited and distance. First time you reach target is the shortest path.",
    ["from collections import deque",
     "",
     "def bfs_shortest(graph, src, target):",
     "    queue = deque([(src, 0)])",
     "    seen = {src}",
     "    while queue:",
     "        node, dist = queue.popleft()",
     "        if node == target:",
     "            return dist",
     "        for nb in graph.get(node, []):",
     "            if nb not in seen:",
     "                seen.add(nb)",
     "                queue.append((nb, dist + 1))",
     "    return -1"])


def _dfs_reachable(): return _topic(
    "qx2_dfs_reach_v2",
    ["Check if 4 is reachable from 1 in {1:[2,3], 2:[4], 3:[4]}.",
     "Check if 5 is reachable from 1 in {1:[2,3], 2:[4], 3:[4]}.",
     "Check if 1 is reachable from 1."],
    "DFS or BFS through the graph; track visited. Return True if target is reached.",
    ["def dfs_reachable(graph, src, target):",
     "    if src == target:",
     "        return True",
     "    seen = {src}",
     "    stack = [src]",
     "    while stack:",
     "        node = stack.pop()",
     "        for nb in graph.get(node, []):",
     "            if nb == target:",
     "                return True",
     "            if nb not in seen:",
     "                seen.add(nb)",
     "                stack.append(nb)",
     "    return False"])


def _dijkstra(): return _topic(
    "qx2_dijkstra_v2",
    ["Shortest path from A to D in {A:{B:1,C:4}, B:{C:2,D:5}, C:{D:1}}.",
     "Shortest from 0 to 4 in {0:{1:1,2:4},1:{2:2,3:5},2:{3:1,4:7},3:{4:3},4:{}}.",
     "Shortest from X to Y in {X:{Y:10},Y:{}}."],
    "Min-heap of (distance, node). Pop smallest, relax neighbors, push updates. Track dist dict.",
    ["import heapq",
     "",
     "def dijkstra(graph, src, target):",
     "    dist = {src: 0}",
     "    heap = [(0, src)]",
     "    while heap:",
     "        d, u = heapq.heappop(heap)",
     "        if u == target:",
     "            return d",
     "        if d > dist.get(u, float('inf')):",
     "            continue",
     "        for v, w in graph.get(u, {}).items():",
     "            nd = d + w",
     "            if nd < dist.get(v, float('inf')):",
     "                dist[v] = nd",
     "                heapq.heappush(heap, (nd, v))",
     "    return -1"])


def _topological_sort(): return _topic(
    "qx2_topo_sort_v2",
    ["Topological order of {0:[], 1:[], 2:[3], 3:[1], 4:[0,1], 5:[0,2]}.",
     "Topological order of single node.",
     "Topological order with two parallel chains."],
    "Kahn's algorithm: in-degrees, push zero-indegree nodes, pop and decrement neighbors.",
    ["from collections import deque, defaultdict",
     "",
     "def topo_sort(graph):",
     "    indeg = defaultdict(int)",
     "    for u in graph:",
     "        for v in graph[u]:",
     "            indeg[v] += 1",
     "    queue = deque(u for u in graph if indeg[u] == 0)",
     "    order = []",
     "    while queue:",
     "        u = queue.popleft()",
     "        order.append(u)",
     "        for v in graph[u]:",
     "            indeg[v] -= 1",
     "            if indeg[v] == 0:",
     "                queue.append(v)",
     "    return order"])


def _detect_cycle_directed(): return _topic(
    "qx2_cycle_directed_v2",
    ["Detect cycle in {0:[1], 1:[2], 2:[0]}.",
     "Detect cycle in {0:[1], 1:[2], 2:[3]}.",
     "Detect cycle in {}."],
    "DFS with three colors (white/gray/black). A back-edge to a gray node means cycle.",
    ["def has_cycle(graph):",
     "    WHITE, GRAY, BLACK = 0, 1, 2",
     "    color = {u: WHITE for u in graph}",
     "    def dfs(u):",
     "        color[u] = GRAY",
     "        for v in graph[u]:",
     "            if color.get(v, WHITE) == GRAY:",
     "                return True",
     "            if color[v] == WHITE and dfs(v):",
     "                return True",
     "        color[u] = BLACK",
     "        return False",
     "    for u in list(graph):",
     "        if color[u] == WHITE and dfs(u):",
     "            return True",
     "    return False"])


def _union_find_basic(): return _topic(
    "qx2_union_find_v2",
    ["Union (1,2),(2,3),(4,5); find(1)==find(3)? True.",
     "After union (1,2), find(1) and find(2) should be equal.",
     "After union (1,2),(3,4); find(1) and find(3) should differ."],
    "Path-compressed union-find. Each node points to a parent; union joins two roots; find compresses paths.",
    ["class UF:",
     "    def __init__(self):",
     "        self.p = {}",
     "    def find(self, x):",
     "        if x not in self.p:",
     "            self.p[x] = x",
     "        while self.p[x] != x:",
     "            self.p[x] = self.p[self.p[x]]",
     "            x = self.p[x]",
     "        return x",
     "    def union(self, a, b):",
     "        ra, rb = self.find(a), self.find(b)",
     "        if ra != rb:",
     "            self.p[ra] = rb"])


def _kruskal_mst(): return _topic(
    "qx2_kruskal_v2",
    ["Compute MST weight for edges [(0,1,10),(0,2,6),(0,3,5),(1,3,15),(2,3,4)].",
     "Compute MST weight for two isolated triangles.",
     "Compute MST weight for a single edge."],
    "Sort edges by weight. Greedily add edges that don't form a cycle (via union-find).",
    ["def kruskal(n, edges):",
     "    uf = UF()",
     "    mst = []",
     "    for u, v, w in sorted(edges, key=lambda e: e[2]):",
     "        if uf.find(u) != uf.find(v):",
     "            uf.union(u, v)",
     "            mst.append((u, v, w))",
     "    return mst"])


def _prim_mst(): return _topic(
    "qx2_prim_v2",
    ["Compute MST edges starting from 0 for graph with edges {(0,1,4),(0,2,3),(1,2,1),(2,3,2),(3,4,5)}.",
     "Compute MST for a 3-node triangle.",
     "Compute MST for an empty graph."],
    "Start from any node. Repeatedly pick the cheapest edge that connects a new node.",
    ["import heapq",
     "",
     "def prim(graph, start=0):",
     "    visited = {start}",
     "    edges = [(w, start, v) for v, w in graph[start]]",
     "    heapq.heapify(edges)",
     "    mst = []",
     "    while edges:",
     "        w, u, v = heapq.heappop(edges)",
     "        if v in visited:",
     "            continue",
     "        visited.add(v)",
     "        mst.append((u, v, w))",
     "        for nb, w2 in graph[v]:",
     "            if nb not in visited:",
     "                heapq.heappush(edges, (w2, v, nb))",
     "    return mst"])


def _bellman_ford(): return _topic(
    "qx2_bellman_ford_v2",
    ["Find shortest path from 0 to 3 in graph with edges [(0,1,1),(1,2,-1),(2,3,-1),(0,3,4)].",
     "Find shortest from 0 to 1 in simple 2-node graph.",
     "Detect negative cycle in {0:[1,-1],1:[0,-1]}."],
    "Relax all edges (n-1) times. If any distance still improves on the n-th pass, there's a negative cycle.",
    ["def bellman_ford(n, edges, src):",
     "    dist = [float('inf')] * n",
     "    dist[src] = 0",
     "    for _ in range(n - 1):",
     "        for u, v, w in edges:",
     "            if dist[u] + w < dist[v]:",
     "                dist[v] = dist[u] + w",
     "    return dist"])


def _lru_cache_impl(): return _topic(
    "qx2_lru_cache_v2",
    ["Implement an LRU cache of capacity 2. Add 1,2,3 -> cache is {2,3}.",
     "Get key 1 in the same cache; should return -1 (evicted).",
     "Update a value; should not affect recency order."],
    "Hashmap for O(1) lookup + doubly-linked list for O(1) eviction. Move accessed items to the front.",
    ["class LRUCache:",
     "    def __init__(self, capacity):",
     "        self.cap = capacity",
     "        self.cache = {}",
     "    def get(self, k):",
     "        if k not in self.cache:",
     "            return -1",
     "        v = self.cache.pop(k)",
     "        self.cache[k] = v",
     "        return v",
     "    def put(self, k, v):",
     "        if k in self.cache:",
     "            self.cache.pop(k)",
     "        self.cache[k] = v",
     "        if len(self.cache) > self.cap:",
     "            self.cache.pop(next(iter(self.cache)))"])


def _lfu_cache_impl(): return _topic(
    "qx2_lfu_cache_v2",
    ["Implement an LFU cache of capacity 2 with operations put(1,1), put(2,2), get(1), put(3,3) -> (2,-1) (3,3).",
     "Single key; get returns its value.",
     "Empty cache; get returns -1."],
    "Track frequency per key. On eviction, remove the least-frequently-used; tie-break on oldest.",
    ["from collections import defaultdict",
     "",
     "class LFUCache:",
     "    def __init__(self, capacity):",
     "        self.cap = capacity",
     "        self.vals = {}",
     "        self.freq = defaultdict(int)",
     "    def get(self, k):",
     "        if k not in self.vals:",
     "            return -1",
     "        self.freq[k] += 1",
     "        return self.vals[k]",
     "    def put(self, k, v):",
     "        if self.cap == 0:",
     "            return",
     "        if k in self.vals:",
     "            self.vals[k] = v",
     "            self.freq[k] += 1",
     "            return",
     "        if len(self.vals) >= self.cap:",
     "            evict = min(self.freq, key=self.freq.get)",
     "            del self.vals[evict]",
     "            del self.freq[evict]",
     "        self.vals[k] = v",
     "        self.freq[k] = 1"])


def _fib_memoized(): return _topic(
    "qx2_fib_memo_v2",
    ["Compute fib(30) with memoization.",
     "Compute fib(10).",
     "Compute fib(0)."],
    "Top-down DP with memoization. Cache computed results; fib(n) = fib(n-1) + fib(n-2).",
    ["def fib(n, memo={}):",
     "    if n in memo:",
     "        return memo[n]",
     "    if n < 2:",
     "        return n",
     "    memo[n] = fib(n - 1, memo) + fib(n - 2, memo)",
     "    return memo[n]"])


def _fib_iterative(): return _topic(
    "qx2_fib_iter_v2",
    ["Compute fib(50) iteratively.",
     "Compute fib(0) iteratively.",
     "Compute fib(1) iteratively."],
    "Bottom-up DP: maintain just two variables. O(n) time, O(1) space.",
    ["def fib(n):",
     "    if n < 2:",
     "        return n",
     "    a, b = 0, 1",
     "    for _ in range(n):",
     "        a, b = b, a + b",
     "    return a"])


def _lis_length(): return _topic(
    "qx2_lis_v2",
    ["Find LIS length in [10, 9, 2, 5, 3, 7, 101, 18]; answer 4.",
     "Find LIS length in [0, 1, 0, 3, 2, 3]; answer 4.",
     "Find LIS length in [7, 7, 7, 7]; answer 1."],
    "Patience sorting: maintain a tails array. For each x, find the leftmost tail >= x and replace it. O(n log n).",
    ["import bisect",
     "",
     "def length_of_lis(nums):",
     "    tails = []",
     "    for x in nums:",
     "        i = bisect.bisect_left(tails, x)",
     "        if i == len(tails):",
     "            tails.append(x)",
     "        else:",
     "            tails[i] = x",
     "    return len(tails)"])


def _matrix_rotation(): return _topic(
    "qx2_matrix_rotate_v2",
    ["Rotate [[1,2,3],[4,5,6],[7,8,9]] 90 degrees clockwise.",
     "Rotate a 2x2 [[1,2],[3,4]].",
     "Rotate a 1x1 [[1]]."],
    "Transpose then reverse each row. O(n^2) for nxn.",
    ["def rotate_matrix(m):",
     "    n = len(m)",
     "    for i in range(n):",
     "        for j in range(i + 1, n):",
     "            m[i][j], m[j][i] = m[j][i], m[i][j]",
     "    for row in m:",
     "        row.reverse()",
     "    return m"])


def _spiral_matrix(): return _topic(
    "qx2_spiral_v2",
    ["Return spiral order of [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5].",
     "Return spiral order of [[1,2],[3,4]].",
     "Return spiral order of [[1]]."],
    "Track four boundaries: top, bottom, left, right. Traverse in shrinking rings.",
    ["def spiral_order(matrix):",
     "    out = []",
     "    top, bot = 0, len(matrix) - 1",
     "    left, right = 0, len(matrix[0]) - 1",
     "    while top <= bot and left <= right:",
     "        for j in range(left, right + 1):",
     "            out.append(matrix[top][j])",
     "        top += 1",
     "        for i in range(top, bot + 1):",
     "            out.append(matrix[i][right])",
     "        right -= 1",
     "        if top <= bot:",
     "            for j in range(right, left - 1, -1):",
     "                out.append(matrix[bot][j])",
     "            bot -= 1",
     "        if left <= right:",
     "            for i in range(bot, top - 1, -1):",
     "                out.append(matrix[i][left])",
     "            left += 1",
     "    return out"])


def _jump_game(): return _topic(
    "qx2_jump_game_v2",
    ["Can reach end of [2, 3, 1, 1, 4]? Yes.",
     "Can reach end of [3, 2, 1, 0, 4]? No.",
     "Can reach end of [0]? Yes (already at end)."],
    "Greedy: track the farthest reachable index. If current index exceeds farthest, return False.",
    ["def can_jump(nums):",
     "    reach = 0",
     "    for i, n in enumerate(nums):",
     "        if i > reach:",
     "            return False",
     "        reach = max(reach, i + n)",
     "    return True"])


def _jump_game_ii(): return _topic(
    "qx2_jump_min_v2",
    ["Min jumps to reach end of [2, 3, 1, 1, 4]; answer 2.",
     "Min jumps for [2, 3, 0, 1, 4]; answer 2.",
     "Min jumps for [1, 2, 3]; answer 2."],
    "Greedy: maintain current_end and farthest in the current range. When i reaches current_end, increment jumps and update.",
    ["def jump(nums):",
     "    if len(nums) <= 1:",
     "        return 0",
     "    jumps = 0",
     "    cur_end = 0",
     "    farthest = 0",
     "    for i, n in enumerate(nums[:-1]):",
     "        farthest = max(farthest, i + n)",
     "        if i == cur_end:",
     "            jumps += 1",
     "            cur_end = farthest",
     "    return jumps"])


def _merge_intervals(): return _topic(
    "qx2_merge_intervals_v2",
    ["Merge [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]].",
     "Merge [[1,4],[4,5]] -> [[1,5]].",
     "Merge [[1,4],[0,4]] -> [[0,4]]."],
    "Sort by start. Walk through; extend current interval if it overlaps, otherwise start a new one.",
    ["def merge_intervals(intervals):",
     "    intervals.sort()",
     "    out = []",
     "    for s, e in intervals:",
     "        if out and s <= out[-1][1]:",
     "            out[-1][1] = max(out[-1][1], e)",
     "        else:",
     "            out.append([s, e])",
     "    return out"])


def _insert_interval(): return _topic(
    "qx2_insert_interval_v2",
    ["Insert [4,8] into [[1,2],[3,5],[6,7],[9,10]] -> [[1,2],[3,8],[9,10]].",
     "Insert [2,5] into [[1,3],[6,9]] -> [[1,5],[6,9]].",
     "Insert [3,4] into empty intervals."],
    "Walk through intervals; add before/overlap/after segments to a result list.",
    ["def insert(intervals, new):",
     "    out = []",
     "    for i in intervals:",
     "        if i[1] < new[0]:",
     "            out.append(i)",
     "        elif i[0] > new[1]:",
     "            out.append(new)",
     "            new = i",
     "        else:",
     "            new[0] = min(new[0], i[0])",
     "            new[1] = max(new[1], i[1])",
     "    out.append(new)",
     "    return out"])


def _word_ladder(): return _topic(
    "qx2_word_ladder_v2",
    ["Min transformations from 'hit' to 'cog' using {'hot','dot','dog','lot','log','cog'}.",
     "Min transformations from 'hot' to 'dot'.",
     "Min transformations from 'a' to 'c' using {'b','c'}."],
    "BFS from begin word. For each current word, try all one-letter variants present in the set.",
    ["from collections import deque",
     "",
     "def ladder_length(begin, end, words):",
     "    s = set(words)",
     "    queue = deque([(begin, 1)])",
     "    while queue:",
     "        word, depth = queue.popleft()",
     "        if word == end:",
     "            return depth",
     "        for i in range(len(word)):",
     "            for c in 'abcdefghijklmnopqrstuvwxyz':",
     "                nw = word[:i] + c + word[i+1:]",
     "                if nw in s:",
     "                    s.remove(nw)",
     "                    queue.append((nw, depth + 1))",
     "    return 0"])


def _longest_consecutive(): return _topic(
    "qx2_longest_consec_v2",
    ["Find longest consecutive sequence in [100, 4, 200, 1, 3, 2]; answer 4.",
     "Find it in [0, -1]; answer 2.",
     "Find it in [1, 2, 0, 1]; answer 3."],
    "Insert all into a set. For each num, expand only if num-1 is not in the set (start of a sequence).",
    ["def longest_consecutive(nums):",
     "    s = set(nums)",
     "    best = 0",
     "    for n in s:",
     "        if n - 1 not in s:",
     "            length = 0",
     "            while n + length in s:",
     "                length += 1",
     "            best = max(best, length)",
     "    return best"])


def _max_area_histogram(): return _topic(
    "qx2_max_histogram_v2",
    ["Largest rectangle in histogram [2, 1, 5, 6, 2, 3]; answer 10.",
     "Largest in [2, 4]; answer 4.",
     "Largest in [1]; answer 1."],
    "Monotonic stack of indices with increasing heights. For each popped bar, compute the area using the new bounds.",
    ["def largest_rectangle(heights):",
     "    stack = []",
     "    best = 0",
     "    for i, h in enumerate(heights + [0]):",
     "        while stack and heights[stack[-1]] >= h:",
     "            top = stack.pop()",
     "            width = i if not stack else i - stack[-1] - 1",
     "            best = max(best, heights[top] * width)",
     "        stack.append(i)",
     "    return best"])


def _trapping_rain_ii(): return _topic(
    "qx2_trap_rain_2d_v2",
    ["Trap rain in 2D heights given an mxn matrix.",
     "Trap rain in a 1x1 grid; answer 0.",
     "Trap rain in a uniform 3x3 of 1s; answer 0."],
    "BFS from the boundary using a min-heap. Pop the lowest cell; raise it to be a wall if needed.",
    ["import heapq",
     "",
     "def trap_2d(heights):",
     "    if not heights or not heights[0]:",
     "        return 0",
     "    m, n = len(heights), len(heights[0])",
     "    visited = [[False] * n for _ in range(m)]",
     "    heap = []",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if i in (0, m - 1) or j in (0, n - 1):",
     "                heapq.heappush(heap, (heights[i][j], i, j))",
     "                visited[i][j] = True",
     "    water = 0",
     "    while heap:",
     "        h, i, j = heapq.heappop(heap)",
     "        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):",
     "            ni, nj = i + di, j + dj",
     "            if 0 <= ni < m and 0 <= nj < n and not visited[ni][nj]:",
     "                visited[ni][nj] = True",
     "                nh = heights[ni][nj]",
     "                if nh < h:",
     "                    water += h - nh",
     "                    nh = h",
     "                heapq.heappush(heap, (nh, ni, nj))",
     "    return water"])


def _count_islands(): return _topic(
    "qx2_count_islands_v2",
    ["Count islands in [['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]; answer 3.",
     "Count islands in [['1','1','1']]; answer 1.",
     "Count islands in [['0','0']]; answer 0."],
    "DFS from each unvisited '1'; sink the whole island by marking visited. Increment counter.",
    ["def num_islands(grid):",
     "    if not grid:",
     "        return 0",
     "    m, n = len(grid), len(grid[0])",
     "    count = 0",
     "    def sink(i, j):",
     "        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] != '1':",
     "            return",
     "        grid[i][j] = '0'",
     "        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):",
     "            sink(i + di, j + dj)",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if grid[i][j] == '1':",
     "                sink(i, j)",
     "                count += 1",
     "    return count"])


def _rotting_oranges(): return _topic(
    "qx2_rotting_v2",
    ["Minutes to rot all oranges in [[2,1,1],[1,1,0],[0,1,1]]; answer 4.",
     "Minutes for empty grid; answer 0.",
     "Minutes for grid with no fresh oranges; answer 0."],
    "Multi-source BFS from initially rotten oranges. Each minute spreads to 4-neighbors; track elapsed minutes.",
    ["from collections import deque",
     "",
     "def oranges_rotting(grid):",
     "    m, n = len(grid), len(grid[0])",
     "    queue = deque()",
     "    fresh = 0",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if grid[i][j] == 2:",
     "                queue.append((i, j, 0))",
     "            elif grid[i][j] == 1:",
     "                fresh += 1",
     "    minutes = 0",
     "    while queue:",
     "        i, j, t = queue.popleft()",
     "        minutes = t",
     "        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):",
     "            ni, nj = i + di, j + dj",
     "            if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == 1:",
     "                grid[ni][nj] = 2",
     "                fresh -= 1",
     "                queue.append((ni, nj, t + 1))",
     "    return minutes if fresh == 0 else -1"])


def _matrix_zero_set(): return _topic(
    "qx2_set_zero_v2",
    ["Set rows and cols to 0 in [[1,1,1],[1,0,1],[1,1,1]] -> [[1,0,1],[0,0,0],[1,0,1]].",
     "Set zeros in 1x1 [[0]] -> [[0]].",
     "Set zeros in all-1s -> all-1s (no change)."],
    "First pass: mark which rows/cols have a zero. Second pass: zero them out.",
    ["def set_zeroes(matrix):",
     "    m, n = len(matrix), len(matrix[0])",
     "    rows, cols = set(), set()",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if matrix[i][j] == 0:",
     "                rows.add(i)",
     "                cols.add(j)",
     "    for i in rows:",
     "        for j in range(n):",
     "            matrix[i][j] = 0",
     "    for j in cols:",
     "        for i in range(m):",
     "            matrix[i][j] = 0",
     "    return matrix"])


def _search_2d_matrix(): return _topic(
    "qx2_search_2d_v2",
    ["Search 14 in [[1,3,5,7],[10,11,16,20],[23,30,34,60]]; True.",
     "Search 13 in same matrix; False.",
     "Search 1 in same matrix; True."],
    "Treat the matrix as a flattened sorted array. Binary search on (i*m + j) mapping.",
    ["def search_matrix(matrix, target):",
     "    if not matrix:",
     "        return False",
     "    m, n = len(matrix), len(matrix[0])",
     "    lo, hi = 0, m * n - 1",
     "    while lo <= hi:",
     "        mid = (lo + hi) // 2",
     "        val = matrix[mid // n][mid % n]",
     "        if val == target:",
     "            return True",
     "        if val < target:",
     "            lo = mid + 1",
     "        else:",
     "            hi = mid - 1",
     "    return False"])


def _search_2d_matrix_ii(): return _topic(
    "qx2_search_2d_ii_v2",
    ["Search 5 in [[1,4,7,11],[2,5,8,12],[3,6,9,16],[10,13,14,17]]; True.",
     "Search 20 in same matrix; False.",
     "Search 15 in same matrix; True."],
    "Start at top-right or bottom-left. Eliminate a row or column each step.",
    ["def search_matrix_ii(matrix, target):",
     "    if not matrix:",
     "        return False",
     "    i, j = 0, len(matrix[0]) - 1",
     "    while i < len(matrix) and j >= 0:",
     "        v = matrix[i][j]",
     "        if v == target:",
     "            return True",
     "        if v > target:",
     "            j -= 1",
     "        else:",
     "            i += 1",
     "    return False"])


def _min_path_sum(): return _topic(
    "qx2_min_path_v2",
    ["Min path sum in [[1,3,1],[1,5,1],[4,2,1]] -> 7.",
     "Min path in 1x1 [[5]] -> 5.",
     "Min path in 1x3 [[1,2,3]] -> 6."],
    "DP: dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]).",
    ["def min_path_sum(grid):",
     "    m, n = len(grid), len(grid[0])",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if i == 0 and j == 0:",
     "                continue",
     "            elif i == 0:",
     "                grid[i][j] += grid[i][j-1]",
     "            elif j == 0:",
     "                grid[i][j] += grid[i-1][j]",
     "            else:",
     "                grid[i][j] += min(grid[i-1][j], grid[i][j-1])",
     "    return grid[-1][-1]"])


def _unique_paths(): return _topic(
    "qx2_unique_paths_v2",
    ["Count unique paths in a 3x7 grid.",
     "Count paths in a 3x3 grid; answer 6.",
     "Count paths in a 1x1 grid; answer 1."],
    "Combinatorics: m+n-2 choose n-1. Or DP.",
    ["from math import comb",
     "",
     "def unique_paths(m, n):",
     "    return comb(m + n - 2, n - 1)"])


def _unique_paths_ii(): return _topic(
    "qx2_unique_paths_obstacles_v2",
    ["Count paths in [[0,0,0],[0,1,0],[0,0,0]] -> 2.",
     "Count paths in 1x1 with obstacle; 0.",
     "Count paths in 3x3 with no obstacles; 6."],
    "DP; cells with obstacles contribute 0 paths.",
    ["def unique_paths_with_obstacles(grid):",
     "    m, n = len(grid), len(grid[0])",
     "    if grid[0][0] == 1:",
     "        return 0",
     "    dp = [[0] * n for _ in range(m)]",
     "    dp[0][0] = 1",
     "    for i in range(m):",
     "        for j in range(n):",
     "            if grid[i][j] == 1:",
     "                dp[i][j] = 0",
     "                continue",
     "            if i:",
     "                dp[i][j] += dp[i-1][j]",
     "            if j:",
     "                dp[i][j] += dp[i][j-1]",
     "    return dp[-1][-1]"])


def _edit_distance(): return _topic(
    "qx2_edit_distance_v2",
    ["Edit distance between 'horse' and 'ros'; answer 3.",
     "Between 'intention' and 'execution'; answer 5.",
     "Between '' and 'abc'; answer 3."],
    "Classic DP. dp[i][j] = edit distance of s[:i] and t[:j]. Transitions: insert/delete/replace.",
    ["def edit_distance(s, t):",
     "    m, n = len(s), len(t)",
     "    dp = [[i + j if i * j == 0 else 0 for j in range(n + 1)] for i in range(m + 1)]",
     "    for i in range(1, m + 1):",
     "        for j in range(1, n + 1):",
     "            if s[i-1] == t[j-1]:",
     "                dp[i][j] = dp[i-1][j-1]",
     "            else:",
     "                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])",
     "    return dp[m][n]"])


def _longest_common_subsequence(): return _topic(
    "qx2_lcs_v2",
    ["LCS of 'abcde' and 'ace'; answer 3.",
     "LCS of 'abc' and 'abc'; answer 3.",
     "LCS of 'abc' and 'def'; answer 0."],
    "DP: dp[i][j] = LCS of s[:i] and t[:j]. If equal, extend; else take max.",
    ["def lcs_v2(s, t):",
     "    m, n = len(s), len(t)",
     "    dp = [[0] * (n + 1) for _ in range(m + 1)]",
     "    for i in range(1, m + 1):",
     "        for j in range(1, n + 1):",
     "            if s[i-1] == t[j-1]:",
     "                dp[i][j] = dp[i-1][j-1] + 1",
     "            else:",
     "                dp[i][j] = max(dp[i-1][j], dp[i][j-1])",
     "    return dp[m][n]"])


def _longest_common_substring(): return _topic(
    "qx2_lcs_substr_v2",
    ["Longest common substring of 'ABABC' and 'BABCA'; answer 4.",
     "Longest of 'abc' and 'def'; answer 0.",
     "Longest of 'same' and 'same'; answer 4."],
    "DP: dp[i][j] = length ending at s[i-1], t[j-1]. Reset to 0 on mismatch. Track max.",
    ["def lcs_substring(s, t):",
     "    m, n = len(s), len(t)",
     "    best = 0",
     "    dp = [[0] * (n + 1) for _ in range(m + 1)]",
     "    for i in range(1, m + 1):",
     "        for j in range(1, n + 1):",
     "            if s[i-1] == t[j-1]:",
     "                dp[i][j] = dp[i-1][j-1] + 1",
     "                best = max(best, dp[i][j])",
     "    return best"])


def _palindromic_subseq(): return _topic(
    "qx2_pal_subseq_v2",
    ["Longest palindromic subsequence of 'bbbab'; answer 4.",
     "Longest of 'cbbd'; answer 2.",
     "Longest of 'a'; answer 1."],
    "DP on length: palindrome[i][j] = palindrome[i+1][j-1] + 2 if s[i]==s[j] else max of the two subproblems.",
    ["def longest_pal_subseq(s):",
     "    n = len(s)",
     "    dp = [1] * n",
     "    for i in range(n - 1, -1, -1):",
     "        new = dp[:]",
     "        for j in range(i + 1, n):",
     "            if s[i] == s[j]:",
     "                new[j] = dp[j-1] + 2 if i + 1 <= j - 1 else 2",
     "            else:",
     "                new[j] = max(dp[j], new[j-1])",
     "        dp = new",
     "    return dp[-1]"])


def _regular_expression(): return _topic(
    "qx2_regex_match_v2",
    ["Match 'aab' with pattern 'c*a*b'.",
     "Match 'mississippi' with 'mis*is*p*.'.",
     "Match 'ab' with '.*'."],
    "DP. '.' matches any char; '*' matches zero or more of the preceding element.",
    ["def is_match(s, p):",
     "    m, n = len(s), len(p)",
     "    dp = [[False] * (n + 1) for _ in range(m + 1)]",
     "    dp[0][0] = True",
     "    for j in range(2, n + 1, 2):",
     "        if p[j-1] == '*' and dp[0][j-2]:",
     "            dp[0][j] = True",
     "    for i in range(1, m + 1):",
     "        for j in range(1, n + 1):",
     "            if p[j-1] == '*':",
     "                dp[i][j] = dp[i][j-2]",
     "                if p[j-2] == '.' or p[j-2] == s[i-1]:",
     "                    dp[i][j] = dp[i][j] or dp[i-1][j]",
     "            elif p[j-1] == '.' or p[j-1] == s[i-1]:",
     "                dp[i][j] = dp[i-1][j-1]",
     "    return dp[m][n]"])


def _wildcard_match(): return _topic(
    "qx2_wildcard_v2",
    ["Match 'aa' with 'a'.",
     "Match 'aa' with '*'.",
     "Match 'cb' with '?a'."],
    "DP similar to regex but '*' here matches any sequence (including empty); '?' matches single char.",
    ["def is_match(s, p):",
     "    m, n = len(s), len(p)",
     "    dp = [[False] * (n + 1) for _ in range(m + 1)]",
     "    dp[0][0] = True",
     "    for j in range(1, n + 1):",
     "        if p[j-1] == '*':",
     "            dp[0][j] = dp[0][j-1]",
     "    for i in range(1, m + 1):",
     "        for j in range(1, n + 1):",
     "            if p[j-1] == '*':",
     "                dp[i][j] = dp[i-1][j] or dp[i][j-1]",
     "            elif p[j-1] == '?' or p[j-1] == s[i-1]:",
     "                dp[i][j] = dp[i-1][j-1]",
     "    return dp[m][n]"])


# Group: math/geometry/algorithms ----------------------------------------------
def _gcd_euclid(): return _topic(
    "qx2_gcd_euclid_v2",
    ["Compute gcd(48, 18); answer 6.",
     "Compute gcd(7, 13); answer 1.",
     "Compute gcd(0, 5); answer 5."],
    "Euclidean algorithm: gcd(a, b) = gcd(b, a % b) until b == 0.",
    ["def gcd(a, b):",
     "    while b:",
     "        a, b = b, a % b",
     "    return a"])


def _lcm_basic(): return _topic(
    "qx2_lcm_basic_v2",
    ["Compute lcm(4, 6); answer 12.",
     "Compute lcm(3, 5); answer 15.",
     "Compute lcm(0, 5); answer 0."],
    "LCM via gcd: lcm(a, b) = abs(a*b) // gcd(a, b). Special case for 0.",
    ["def lcm(a, b):",
     "    if a == 0 or b == 0:",
     "        return 0",
     "    return abs(a * b) // gcd(a, b)"])


def _is_prime(): return _topic(
    "qx2_is_prime_v2",
    ["Is 17 prime? True.",
     "Is 4 prime? False.",
     "Is 1 prime? False."],
    "Trial division up to sqrt(n). Skip even numbers after 2.",
    ["def is_prime(n):",
     "    if n < 2:",
     "        return False",
     "    if n < 4:",
     "        return True",
     "    if n % 2 == 0:",
     "        return False",
     "    i = 3",
     "    while i * i <= n:",
     "        if n % i == 0:",
     "            return False",
     "        i += 2",
     "    return True"])


def _sieve(): return _topic(
    "qx2_sieve_v2",
    ["List primes below 30: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29].",
     "List primes below 10.",
     "List primes below 2: empty."],
    "Sieve of Eratosthenes: mark multiples of each prime starting at p*p.",
    ["def primes_below(n):",
     "    if n <= 2:",
     "        return []",
     "    sieve = [True] * n",
     "    sieve[0] = sieve[1] = False",
     "    for i in range(2, int(n ** 0.5) + 1):",
     "        if sieve[i]:",
     "            for j in range(i * i, n, i):",
     "                sieve[j] = False",
     "    return [i for i in range(n) if sieve[i]]"])


def _power(): return _topic(
    "qx2_pow_v2",
    ["Compute 2**10 = 1024.",
     "Compute 3**4 = 81.",
     "Compute 5**0 = 1."],
    "Fast exponentiation: square and multiply. O(log n) multiplications.",
    ["def power(b, e):",
     "    result = 1",
     "    while e:",
     "        if e & 1:",
     "            result *= b",
     "        b *= b",
     "        e >>= 1",
     "    return result"])


def _sqrt(): return _topic(
    "qx2_sqrt_v2",
    ["Compute floor(sqrt(16)) = 4.",
     "Compute floor(sqrt(15)) = 3.",
     "Compute floor(sqrt(0)) = 0."],
    "Newton's method: x_{n+1} = (x_n + n/x_n) / 2. Converges quadratically.",
    ["def my_sqrt(n):",
     "    if n < 2:",
     "        return n",
     "    x = n",
     "    while True:",
     "        nx = (x + n // x) // 2",
     "        if nx >= x:",
     "            return x",
     "        x = nx"])


# Concatenate all topics --------------------------------------------------------
D_TOPICS = [
    _two_sum(),
    _max_subarray(),
    _product_except_self(),
    _contains_duplicate(),
    _best_time_stock(),
    _climb_stairs(),
    _valid_parens(),
    _group_anagrams(),
    _longest_substring_no_repeat(),
    _top_k_frequent(),
    _reverse_linked_list(),
    _merge_sorted_arrays(),
    _binary_search(),
    _rotate_array(),
    _3sum(),
    _container_most_water(),
    _trapping_rain_water(),
    _min_window_substring(),
    _longest_palindromic_substring(),
    _palindromic_substrings_count(),
    _decode_ways(),
    _word_break(),
    _coin_change(),
    _house_robber(),
    _subset_sum(),
    _bfs_shortest_path(),
    _dfs_reachable(),
    _dijkstra(),
    _topological_sort(),
    _detect_cycle_directed(),
    _union_find_basic(),
    _kruskal_mst(),
    _prim_mst(),
    _bellman_ford(),
    _lru_cache_impl(),
    _lfu_cache_impl(),
    _fib_memoized(),
    _fib_iterative(),
    _lis_length(),
    _matrix_rotation(),
    _spiral_matrix(),
    _jump_game(),
    _jump_game_ii(),
    _merge_intervals(),
    _insert_interval(),
    _word_ladder(),
    _longest_consecutive(),
    _max_area_histogram(),
    _trapping_rain_ii(),
    _count_islands(),
    _rotting_oranges(),
    _matrix_zero_set(),
    _search_2d_matrix(),
    _search_2d_matrix_ii(),
    _min_path_sum(),
    _unique_paths(),
    _unique_paths_ii(),
    _edit_distance(),
    _longest_common_subsequence(),
    _longest_common_substring(),
    _palindromic_subseq(),
    _regular_expression(),
    _wildcard_match(),
    _gcd_euclid(),
    _lcm_basic(),
    _is_prime(),
    _sieve(),
    _power(),
    _sqrt(),
]
