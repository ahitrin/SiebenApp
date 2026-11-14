
# Insert with empty goal description

## Given

we have a goal file with the following content:
```
1   >Example SiebenApp file [2,3,8 /  | ]
2    Subgoal A [4,5 /  | 9]
3    Subgoal B [6,7 /  | ]
4[x] Subgoal A1
5[ ] Subgoal A2
6[ ] Subgoal B1
7    Subgoal B2 [ / 5 | ]
8    [Backlog] [9 /  | ] [Autolink: later:]
9[ ] later: Get rid of A1 [ /  | 4]
```

## When

a user calls `si` with the following arguments:

```shell
si <file.db> insert 2 5 
```

## Then

an utility _exits with code 1_ with the following output:


and the following error:
```
New subgoal description cannot be empty

```

and goal file content will be the following:
```
1   >Example SiebenApp file [2,3,8 /  | ]
2    Subgoal A [4,5 /  | 9]
3    Subgoal B [6,7 /  | ]
4[x] Subgoal A1
5[ ] Subgoal A2
6[ ] Subgoal B1
7    Subgoal B2 [ / 5 | ]
8    [Backlog] [9 /  | ] [Autolink: later:]
9[ ] later: Get rid of A1 [ /  | 4]
```
