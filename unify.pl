#!/usr/bin/swipl

:- dynamic query/1.
:- initialization(run).

writeln(T) :- write(T), nl.

queryAll :-
    forall(query(Q), 
        ( read_term_from_atom(Q, T, [variable_names(L)]),
          ( T -> writeln('1':L) ; writeln('0 ':Q) )
        )).

run :-
    %term_string(Term, "query('A+B+x=b+c+x .')"),
    %term_string(Termx, "query('(1,2,3)=(X,Y,Z).')"),
    current_prolog_flag(argv, Argv),

    %generate the query
    nth0(0, Argv, Q),
    string_concat("query('", Q, Q_temp),
    string_concat(Q_temp, ".')", Q_final),
    term_string(Term_argv, Q_final),
    assert(Term_argv),
    queryAll,
    halt.
