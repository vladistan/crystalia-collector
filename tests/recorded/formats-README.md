Fixture tree for the Phase 7 bookend/zip recorded fixtures and validation checkpoint.

| File       | Format detected | Size      | bookend verdict | Why                                             |
|------------|------------------|-----------|-----------------|--------------------------------------------------|
| small.bin  | none (opaque)    | 35 B      | strong          | size <= 32 KB (D-1 size rule)                    |
| a.zip      | zip              | 208 B     | strong          | size <= 32 KB (size rule; also CD is in tail)    |
| big.jpg    | jpeg             | 40003 B   | weak            | > 32 KB, jpeg carries no strong rule ("opaque")  |

Expected `bookend-strong` / `bookend-weak` counts over this tree: 2 strong, 1 weak.
`a.zip` also yields a `zip-cd` and `zip-manifest` descriptor (its Central Directory
is inside the captured tail); `small.bin` and `big.jpg` yield neither (not zip family).
