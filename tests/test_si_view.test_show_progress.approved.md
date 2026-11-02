
# Show progress

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
si <file.db> view -p
```

## Then

an utility _passes_ with the following output:
> * [ ] **1** Example SiebenApp file [Id: 1,Progress: 11% (1/9)]
>   * [ ] **2** Subgoal A (related to **9**) [Id: 2,Progress: 33% (1/3)]
>     * [ ] **5** Subgoal A2 [Id: 5,Progress: 0% (0/1)]
>   * [ ] **3** Subgoal B [Id: 3,Progress: 0% (0/3)]
>     * [ ] **6** Subgoal B1 [Id: 6,Progress: 0% (0/1)]
>     * [ ] **7** Subgoal B2 (blocked by **5**) [Id: 7,Progress: 0% (0/1)]
>   * [ ] **8** [Backlog] [Autolink: later:,Id: 8,Progress: 0% (0/2)]
>     * [ ] **9** later: Get rid of A1 [Id: 9,Progress: 0% (0/1)]

and the following error:
```

```
