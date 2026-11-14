
# Do not overwrite existing file

## Given

file <file.db> already exists

## When

a user calls `si` with the following arguments:

```shell
si <file.db> new "Root subgoal"
```

## Then

an utility _exits with code 1_ with the following output:


and the following error:
```
File <file.db> already exists!

```

and file content will be the following:
```
<UNKNOWN>
```
