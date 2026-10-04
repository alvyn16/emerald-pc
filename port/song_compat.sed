# ARM GAS uses @ for comments and .word for a 32-bit pointer; x86 GAS
# interprets .word as 16 bits. Keep the generated source in pokeemerald intact.
s/@.*$//
s/\.word([[:space:]])/.long\1/g
