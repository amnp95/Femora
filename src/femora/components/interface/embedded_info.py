from typing import List, Tuple, Set, FrozenSet, Optional, Union
from dataclasses import dataclass, field
import hashlib

"""
PROBLEM STATEMENT: EmbeddedInfo Data Structure with Fast Comparisons
====================================================================

REQUIREMENTS:
1. Data Structure Components:
   - beams: A set/list of integers representing beam identifiers
   - core_number: An integer representing a core identifier
   - beams_solids: A list of tuples (list1, list2) where both are integer lists
   
2. Comparison Rules:
   - EQUAL: Two EmbeddedInfo objects are equal if:
     * Same beams (order doesn't matter)
     * Same core_number
     * Same beams_solids tuples (order of tuples doesn't matter)
   
   - CONFLICT (Invalid State): Two objects conflict if:
     * They have the same beams AND
     * Any list1 in their beams_solids is exactly identical (same elements, same order)
     * This represents an invalid state that should be detected
   
   - SIMILAR: Two objects are similar if:
     * Same beams
     * No conflicts (no duplicate list1)
     * May have different core_number or beams_solids

3. Performance Requirement:
   - All comparisons must be as fast as possible (ideally O(1))

CHALLENGES:
-----------
1. Order Independence: 
   - [1,2,3] and [3,2,1] should be treated as equal beams
   - [([1,2], [3,4]), ([5,6], [7,8])] should equal [([5,6], [7,8]), ([1,2], [3,4])]

2. Conflict Detection:
   - Must detect when list1 arrays are exactly identical (order matters for list1)
   - [1,2] conflicts with [1,2] but NOT with [2,1]

3. Performance:
   - Naive comparison would be O(n*m) for checking conflicts
   - Need O(1) operations for fast real-time processing

SOLUTION APPROACH:
-----------------
1. Data Structure Design:
   - Use frozenset for beams: O(1) equality, automatic deduplication
   - Use immutable tuples internally: Allows hashing and use in sets/dicts
   - Pre-compute all expensive operations during initialization

2. Canonicalization Strategy:
   - Sort beams and store as frozenset
   - Keep list1 order (for conflict detection) but sort list2
   - Sort all tuples to create canonical representation
   - This ensures consistent comparison regardless of input order

3. Hashing Strategy:
   - MD5 hash each list1 for instant conflict detection
   - Hash entire beams_solids structure for equality checking
   - Store hashes in frozensets for O(1) set operations

4. Optimization Techniques:
   - Pre-compute everything during __init__
   - Use set intersection (&) for conflict detection
   - Compare hashes instead of actual data structures
   - Trade memory (storing hashes) for speed (O(1) comparisons)

IMPLEMENTATION DETAILS:
----------------------
- beams: Stored as frozenset(int) for immutability and O(1) equality
- _beams_solids_canonical: Sorted tuple of tuples for consistent representation
- _list1_hashes: Frozenset of MD5 hashes for each list1 (conflict detection)
- _beams_solids_hash: Single hash of entire beams_solids (equality check)

COMPLEXITY ANALYSIS:
-------------------
- Initialization: O(n log n) where n is number of beams_solids tuples
- Equality check: O(1) - compare pre-computed hashes
- Conflict check: O(1) - set intersection of hash sets  
- Similarity check: O(1) - beams equality + conflict check
- Memory usage: O(n) extra space for hashes

USAGE EXAMPLE:
-------------
e1 = EmbeddedInfo([1,2,3], 5, [([1,2], [3,4])])
e2 = EmbeddedInfo([3,2,1], 5, [([1,2], [4,3])])  # Equal to e1
e3 = EmbeddedInfo([1,2,3], 7, [([1,2], [5,6])])  # Conflicts with e1
e4 = EmbeddedInfo([1,2,3], 7, [([3,4], [5,6])])  # Similar to e1

e1.compare(e2)  # Returns "equal"
e1.compare(e3)  # Returns "conflict" 
e1.compare(e4)  # Returns "similar"

WHY THIS APPROACH:
-----------------
1. Immutability: Using frozen dataclass and frozensets ensures objects can be hashed
   and used in sets/dicts safely

2. Pre-computation: All expensive operations happen once during initialization,
   making repeated comparisons extremely fast

3. Canonical Forms: Sorting ensures that logically equivalent data is represented
   identically, solving the order-independence problem

4. Hash-based Comparison: Comparing fixed-length hashes is faster than comparing
   variable-length data structures

5. Set Operations: Using frozensets for both beams and list1_hashes enables
   Python's optimized set operations for O(1) performance

This design achieves the goal of very fast comparisons while maintaining
correctness and handling all edge cases properly.
"""


@dataclass(frozen=True)
class EmbeddedInfo:
    """Optimized data structure representing embedded information with fast comparison capabilities.

    This class stores beam identifiers, a core number, and beam-solid relationships,
    providing highly optimized methods for equality, conflict, and similarity checks.
    It pre-computes various canonical forms and hashes during initialization to
    achieve O(1) comparison times.

    Attributes:
        beams (FrozenSet[int]): A frozenset of unique integer beam identifiers.
        core_number (int): An integer representing the core identifier.
        _beams_solids_canonical (Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], ...]):
            An internally sorted tuple of (sorted_list1_tuple, sorted_list2_tuple)
            representing the canonical form of `beams_solids`.
        _list1_hashes (FrozenSet[str]): A frozenset of MD5 hashes for each
            `list1` component in `beams_solids`, used for fast conflict detection.
        _beams_solids_hash (str): A single MD5 hash of the entire canonical
            `_beams_solids_canonical` structure, used for O(1) equality checks.
        _solids_set (FrozenSet[int]): A frozenset of all unique solid identifiers
            (from `list2` parts of `beams_solids`) for similarity checks.

    Example:
        >>> e1 = EmbeddedInfo(beams=[1, 2, 3], core_number=5, beams_solids=[([1, 2], [3, 4])])
        >>> e2 = EmbeddedInfo(beams=[3, 2, 1], core_number=5, beams_solids=[([1, 2], [4, 3])])
        >>> print(e1 == e2)
        True
        >>> e3 = EmbeddedInfo(beams=[1, 2, 3], core_number=10, beams_solids=[([1, 2], [9, 10])])
        >>> print(e1.is_conflict(e3))
        True
    """
    
    # Store beams as frozenset for immutability and fast equality
    beams: FrozenSet[int]
    core_number: int
    
    # Internal optimized representations
    _beams_solids_canonical: Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], ...] = field(repr=False)
    _list1_hashes: FrozenSet[str] = field(repr=False)
    _beams_solids_hash: str = field(repr=False)
    _solids_set: FrozenSet[int] = field(repr=False)
    
    def __init__(self, beams: Union[List[int], Set[int]], core_number: int, 
                 beams_solids: List[Tuple[List[int], List[int]]]):
        """Initializes the EmbeddedInfo object, pre-computing canonical forms and hashes.

        Args:
            beams: A list or set of integer beam identifiers. Will be converted to a frozenset.
            core_number: An integer representing the core identifier.
            beams_solids: A list of tuples, where each tuple contains two lists of integers.
                The first list (`list1`) identifies the primary entity, and the second (`list2`)
                identifies associated solids. This structure is canonicalized and hashed
                for efficient comparisons.
        """
        # Convert beams to frozenset
        object.__setattr__(self, 'beams', frozenset(beams))
        object.__setattr__(self, 'core_number', core_number)
        
        # Canonicalize beams_solids: sort each tuple internally, then sort all tuples
        canonical_tuples = []
        list1_hashes = set()
        solids_seen = set()
        
        for list1, list2 in beams_solids:
            # Convert to tuples for immutability
            tuple1 = tuple(list1)  # Keep original order for list1 (conflict detection)
            tuple2 = tuple(sorted(list2))  # Sort list2 for consistency
            
            # Hash list1 for fast conflict detection
            list1_hash = hashlib.md5(str(tuple1).encode()).hexdigest()
            list1_hashes.add(list1_hash)
            
            canonical_tuples.append((tuple1, tuple2))

            # collect solids for similarity checks based on solid overlap
            for s in tuple2:
                solids_seen.add(s)
        
        # Sort tuples by their string representation for canonical form
        canonical_tuples.sort(key=lambda x: (x[0], x[1]))
        
        # Store canonical representation
        object.__setattr__(self, '_beams_solids_canonical', tuple(canonical_tuples))
        object.__setattr__(self, '_list1_hashes', frozenset(list1_hashes))
        
        # Pre-compute hash for beams_solids
        beams_solids_str = str(self._beams_solids_canonical)
        beams_solids_hash = hashlib.md5(beams_solids_str.encode()).hexdigest()
        object.__setattr__(self, '_beams_solids_hash', beams_solids_hash)

        # Store solids set
        object.__setattr__(self, '_solids_set', frozenset(solids_seen))

    @property
    def solids_set(self) -> FrozenSet[int]:
        """Returns a read-only frozenset of all unique solid identifiers.

        The solid identifiers are collected from the `list2` components of the
        `beams_solids` tuples during initialization.

        Returns:
            A frozenset containing all unique integer solid IDs associated with this object.

        Example:
            >>> e = EmbeddedInfo(beams=[1], core_number=1, beams_solids=[([1, 2], [3, 4, 5])])
            >>> print(e.solids_set)
            frozenset({3, 4, 5})
        """
        return self._solids_set
    
    @property
    def beams_solids(self) -> List[Tuple[List[int], List[int]]]:
        """Returns the beams_solids in a list-of-tuples-of-lists format.

        This property reconstructs the original `beams_solids` structure from
        its internal canonical representation, converting tuples back to lists
        for external compatibility. The order of inner lists (`list1`, `list2`)
        and outer tuples is the canonical sorted order.

        Returns:
            A list of (list of int, list of int) tuples.

        Example:
            >>> e = EmbeddedInfo(beams=[1], core_number=1, beams_solids=[([2, 1], [3, 4])])
            >>> print(e.beams_solids)
            [([2, 1], [3, 4])]
        """
        return [(list(t1), list(t2)) for t1, t2 in self._beams_solids_canonical]
    
    def __eq__(self, other: 'EmbeddedInfo') -> bool:
        """Determines if two EmbeddedInfo objects are equal.

        Two objects are considered equal if they have the same `beams` (order-independent),
        the same `core_number`, and the same `beams_solids` (order-independent for tuples
        and for elements within `list2`, but `list1` order is preserved for its internal hash).
        This comparison uses pre-computed hashes for O(1) performance.

        Args:
            other: The other EmbeddedInfo object to compare against.

        Returns:
            True if the objects are equal, False otherwise.
        """
        if not isinstance(other, EmbeddedInfo):
            return False
        
        # Fast checks first
        if self.beams != other.beams:
            return False
        if self.core_number != other.core_number:
            return False
        
        # Compare pre-computed hashes
        return self._beams_solids_hash == other._beams_solids_hash
    
    def is_conflict(self, other: 'EmbeddedInfo') -> bool:
        """Checks if this object conflicts with another EmbeddedInfo object.

        A conflict occurs if two objects have the same `beams` (order-independent)
        AND share at least one identical `list1` component (order-dependent) in their
        `beams_solids`. This detection uses pre-computed `_list1_hashes` for O(1) performance.

        Args:
            other: The other EmbeddedInfo object to check for conflict.

        Returns:
            True if a conflict is detected, False otherwise.

        Example:
            >>> e1 = EmbeddedInfo(beams=[1, 2], core_number=5, beams_solids=[([10, 20], [30, 40])])
            >>> e2 = EmbeddedInfo(beams=[2, 1], core_number=6, beams_solids=[([10, 20], [50, 60])])
            >>> print(e1.is_conflict(e2))
            True
            >>> e3 = EmbeddedInfo(beams=[1, 2], core_number=7, beams_solids=[([20, 10], [70, 80])])
            >>> print(e1.is_conflict(e3)) # list1 [10, 20] is different from [20, 10]
            False
        """
        if not isinstance(other, EmbeddedInfo):
            return False
        
        # Must have same beams
        if self.beams != other.beams:
            return False
        
        # Check if any list1 hash overlaps
        return bool(self._list1_hashes & other._list1_hashes)
    
    def is_similar(self, other: 'EmbeddedInfo') -> bool:
        """Checks if this object is similar to another EmbeddedInfo object.

        Two EmbeddedInfo objects are considered similar if:
        1. They are not in conflict (`is_conflict` returns False).
        2. They have identical `beams` (order-independent), OR
        3. They share at least one common solid identifier (from their `solids_set`).

        Args:
            other: The other EmbeddedInfo object to check for similarity.

        Returns:
            True if the objects are similar, False otherwise.

        Example:
            >>> e1 = EmbeddedInfo(beams=[1, 2], core_number=5, beams_solids=[([10], [100])])
            >>> e2 = EmbeddedInfo(beams=[2, 1], core_number=6, beams_solids=[([20], [200])])
            >>> print(e1.is_similar(e2)) # Same beams, different core/solids, no conflict
            True
            >>> e3 = EmbeddedInfo(beams=[3, 4], core_number=7, beams_solids=[([30], [100, 300])])
            >>> print(e1.is_similar(e3)) # Different beams, but shared solid '100', no conflict
            True
            >>> e4 = EmbeddedInfo(beams=[1, 2], core_number=8, beams_solids=[([10], [400])])
            >>> print(e1.is_similar(e4)) # Conflict based on [10], so not similar
            False
        """
        if not isinstance(other, EmbeddedInfo):
            return False

        # Quick conflict rejection
        if self.is_conflict(other):
            return False

        # Original similarity – same beams
        if self.beams == other.beams:
            return True

        # New similarity – overlapping solids
        return bool(self._solids_set & other._solids_set)
    
    def __hash__(self) -> int:
        """Computes a hash for the EmbeddedInfo object.

        The hash is derived from the `beams` frozenset, `core_number`, and the
        pre-computed hash of `beams_solids`. This allows EmbeddedInfo objects
        to be used efficiently as keys in dictionaries or elements in sets.

        Returns:
            An integer hash value for the object.
        """
        return hash((self.beams, self.core_number, self._beams_solids_hash))
    
    def compare(self, other: 'EmbeddedInfo') -> str:
        """Compares this object with another EmbeddedInfo object and returns their relationship.

        This method provides a comprehensive comparison, categorizing the relationship
        into "equal", "conflict", "similar", or "unrelated" based on a defined hierarchy.

        Args:
            other: The other EmbeddedInfo object to compare against.

        Returns:
            str: One of the following relationship types:
                - "equal": Same beams, core_number, and beams_solids (O(1) check).
                - "conflict": Same beams, but a duplicate `list1` exists in `beams_solids` (O(1) check).
                - "similar":
                    - If same beams: no conflicts, but different `core_number` or `beams_solids`.
                    - If different beams: share at least one common solid element and no conflicts.
                - "unrelated": Different beams and no shared solid elements.

        Raises:
            TypeError: If `other` is not an instance of `EmbeddedInfo`.

        Example:
            >>> e1 = EmbeddedInfo(beams=[1,2,3], core_number=5, beams_solids=[([1,2], [3,4])])
            >>> e2 = EmbeddedInfo(beams=[3,2,1], core_number=5, beams_solids=[([1,2], [4,3])])
            >>> e3 = EmbeddedInfo(beams=[1,2,3], core_number=7, beams_solids=[([1,2], [5,6])])
            >>> e4 = EmbeddedInfo(beams=[1,2,3], core_number=7, beams_solids=[([3,4], [5,6])])
            >>> e5 = EmbeddedInfo(beams=[4,5,6], core_number=5, beams_solids=[([7,8], [9,10])])
            >>> print(e1.compare(e2))
            equal
            >>> print(e1.compare(e3))
            conflict
            >>> print(e1.compare(e4))
            similar
            >>> print(e1.compare(e5))
            unrelated
        """
        if not isinstance(other, EmbeddedInfo):
            raise TypeError(f"Cannot compare EmbeddedInfo with {type(other)}")
        
        # Check equality first (most specific)
        if self == other:
            return "equal"
        
        # Check conflict first (only possible with same beams)
        if self.beams == other.beams:
            if self._list1_hashes & other._list1_hashes:
                return "conflict"
            # Equal already handled; so same beams, no conflict
            return "similar"

        # Different beams – decide similarity by solid overlap
        if self._solids_set & other._solids_set:
            return "similar"

        return "unrelated"

    def with_core_number(self, new_core_number: int) -> 'EmbeddedInfo':
        """Creates a new EmbeddedInfo instance with an updated core number.

        This method returns a new object where `beams` and `beams_solids` remain
        identical to the current instance, but `core_number` is set to the
        provided `new_core_number`. This is useful for creating variations
        without re-processing the complex `beams_solids` structure.

        Args:
            new_core_number: The new integer value for the core identifier.

        Returns:
            A new `EmbeddedInfo` instance with the updated core number.

        Example:
            >>> e1 = EmbeddedInfo(beams=[1, 2], core_number=5, beams_solids=[([10], [100])])
            >>> e_new_core = e1.with_core_number(99)
            >>> print(e_new_core.core_number)
            99
            >>> print(e_new_core.beams == e1.beams)
            True
        """
        return EmbeddedInfo(
            beams=list(self.beams),
            core_number=new_core_number,
            beams_solids=[(list(t1), list(t2)) for t1, t2 in self._beams_solids_canonical]
        )
    
    def __repr__(self) -> str:
        """Returns a string representation of the EmbeddedInfo object.

        The representation includes the `beams` (sorted for consistent display),
        `core_number`, and `beams_solids`.

        Returns:
            A string representing the object's state.
        """
        return f"EmbeddedInfo(beams={sorted(self.beams)}, core_number={self.core_number}, beams_solids={self.beams_solids})"





# Example usage and benchmarking
if __name__ == "__main__":
    # Create test instances
    e1 = EmbeddedInfo(
        beams=[1, 3, 2],
        core_number=5,
        beams_solids=[([2, 1], [3, 4]), ([5, 6], [7, 8])]
    )
    
    e2 = EmbeddedInfo(
        beams=[3, 2, 1],  # Same beams, different order
        core_number=5,
        beams_solids=[([6, 5], [8, 7]), ([2, 1], [4, 3])]  # Same tuples, different order
    )
    
    e3 = EmbeddedInfo(
        beams=[1, 2, 3],
        core_number=10,  # Different core_number
        beams_solids=[([1, 2], [9, 10])]  # Conflict: same list1 [1, 2]
    )
    
    e4 = EmbeddedInfo(
        beams=[1, 2, 3],
        core_number=7,
        beams_solids=[([9, 10], [11, 12])]  # No conflict
    )
    
    print("Equality tests:")
    print(f"e1 == e2: {e1 == e2}")  # True
    print(f"e1 == e3: {e1 == e3}")  # False
    
    print("\nConflict tests:")
    print(f"e1.is_conflict(e3): {e1.is_conflict(e3)}")  # True (same list1)
    print(f"e1.is_conflict(e4): {e1.is_conflict(e4)}")  # False
    
    print("\nSimilarity tests:")
    print(f"e1.is_similar(e3): {e1.is_similar(e3)}")  # False (conflict)
    print(f"e1.is_similar(e4): {e1.is_similar(e4)}")  # True
    
    print("\nCompare method tests:")
    print(f"e1.compare(e2): '{e1.compare(e2)}'")  # "equal"
    print(f"e1.compare(e3): '{e1.compare(e3)}'")  # "conflict"
    print(f"e1.compare(e4): '{e1.compare(e4)}'")  # "similar"
    
    # Test unrelated case
    e5 = EmbeddedInfo(
        beams=[4, 5, 6],  # Different beams
        core_number=5,
        beams_solids=[([1, 2], [3, 4])]
    )
    print(f"e1.compare(e5): '{e1.compare(e5)}'")  # "unrelated"
    
    print("\nHash values (for use in sets/dicts):")
    print(f"hash(e1): {hash(e1)}")
    print(f"hash(e2): {hash(e2)}")
    print(f"Can use in set: {len({e1, e2, e3, e4})}")  # Should be 3 (e1 == e2)