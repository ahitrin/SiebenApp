
# File at unavailable location

## Given

<file.db> points to an unavailable location

## When

a user calls `si` with the following arguments:

```shell
si <file.db> new "Root subgoal"
```

## Then

an utility _exits with code 1_ with the following output:


and the following error:
```
Cannot save file <file.db>

```

and file content will be the following:
```
<UNAVAILABLE>
```
