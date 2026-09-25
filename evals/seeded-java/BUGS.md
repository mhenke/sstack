# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| java-1 | pagination | boundaries | `paginate(items, 0, 2)` | IndexOutOfBoundsException leaks | throw domain error naming page |
| java-2 | pagination | boundaries | empty list | subList bounds error | return empty list or named error |
| java-3 | pricing | missing | null discount | treated as zero silently | documented policy, explicit |
| java-4 | cart | boundaries | `maxQuantity(List.of())` | returns Integer.MIN_VALUE | throw `lines must not be empty` |
| java-5 | cart | malformed | negative quantity | accepts negative max | throw `qty must be positive` |
