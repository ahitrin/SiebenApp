
# Progress + top

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
si <file.db> -p -t
```

## Then

an utility _passes_ with the following output:
> * [ ] **5** Subgoal A2 [Id: 5,Progress: 0% (0/1)]
> * [ ] **6** Subgoal B1 [Id: 6,Progress: 0% (0/1)]
> * [ ] **9** later: Get rid of A1 [Id: 9,Progress: 0% (0/1)]

and the following error:

