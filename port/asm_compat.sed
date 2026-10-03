# Translate ELF-only data directives for the i686 PE/COFF assembler.
s/^[[:space:]]*\.section[[:space:]]+script_data,[[:space:]]*"aw",[[:space:]]*%progbits/.section script_data,"dw"/
/^[[:space:]]*\.size[[:space:]]/d
