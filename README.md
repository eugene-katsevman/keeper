
# Keeper
An extensible console tool for long-term planning.

+[![Join the chat at https://gitter.im/eugene-katsevman/keeper](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/eugene-katsevman/keeper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Keeper is a todo.txt-ish CLI tool for mid and long-term planning. It's main purpose is to tell if you have enough time at your hands.

# Contents

- [Install](#)
- [Basic usage](#)
- [Grouping and queries](#)
- [Attributes](#)
- [AND queries](#)
- [OR queries](#)
- [Combining conditions](#)
- [Special tags --- done, delegated, optional](#)
- [Scheduling](#)
- [TODO file example](#)

# Install
To install Keeper and start using it:
* download or clone it
* create `lists` subdir in keeper's directory
* alias `keeper.py` with something shorter or make a link from `~/bin`. Below I assume you have aliased it as `keeper`.
   
From now on, you might start using it.
# Basic usage
Here are simplest use case:
```bash
keeper edit main
```
Keeper should start a `gedit` session for `lists/main.todo` file. `*.todo` files are task specification files. To check how this works, let's put this line into `main.todo` and then save it.

    My first task

now run `keeper list`. The response should be something like that:

    <main> None My first task [1h]
    Total: 1 task(s), 1 h of worktime

`<main>` is a filename, where our first task is stored.

Tasks are 1 hour long by default. This happens to be very sane assumption, as you'll see later.

Now let us add one more task, now with time spec

    My first task
    My second task 2h

and run `keeper list` again:

    <main> None My first task [1h]
    <main> None My second task 2h [2h]
    Total: 2 task(s), 3 h of worktime

Task duration is extracted from task spec with a simple rule --- everything that looks like integer with _h_ or _m_ at the end is captured as task duration.

# Grouping and queries
The `keeper list` command keeps showing us `None` after the task filename. `None` means our tasks do not belong to any _topic_. Let us fix that now:

    My first task
    My second task 2h
    project1:
        My third task 40m
        My fourth task 4h
    
`keeper list`

    <main> None My first task [1h]
    <main> None My second task 2h [2h]
    <main> project1 My third task 40m [0.67h]
    <main> project1 My fourth task 4h [4h]
    Total: 4 task(s), 7.67 h of worktime

We could list only project1's tasks by doing
>>> keeper list project1

# Attributes
Each task may have different attributes. Task duration is only one of them. There could be **deadlines** , **exact start time**, **periodics** specification, **tags** and some other kinds of attributes.

Attributes are listed in square brackets at any part of task and should be comma-separated from each other. Let us add attributes to our tasks:

    My first task
    My second task 2h [must, <22.10.2015]
    sleep [+22:00, 8h]
    project1:
        My third task 40m [done]
        My fourth task 4h

* Second task now have `must` tag and a deadline
* Sleep occurs every day at 22:00 and lasts for 8 hours
* third task has `done` tag

Any attribute not recognised as special (like _deadline_ or _periodics_, or duration) is assumed to be a _tag name_. _Topics_ actually are tags too. So to query for `must` tasks we could issue next command:

    keeper list must

*.todo file names are tags too. Command `keeper list asdf` will return all tasks from asdf.todo along with all tasks from topic `asdf` and all other tasks marked by `asdf` tag (like **[asdf]**).

# AND queries
To list all tasks, simultaneously having several taks, we should provide a dot-separated list of these tags to `keeper list`:

    keeper list main.must

# OR queries
OR queries are done by providing space-separated list of tags to `keeper list`

# Combining conditions
This command will seek for all done tasks or delegated to alex
    
    keeper list done delegated.alex
    
# Special tags --- done, delegated, optional    

Some tags, like `done` or `delegated`, have special meaning and are omitted from output by default. So plain `keeper list` will only list tasks yet to be completed and not delegated. To list such tasks we must add this special task to query like this:

    keeper list main.must.done

This will list done tasks from main having tag `must`

# Scheduling
Deadline attributes looks like `<date` or `<date time`. I.e. `<12.04.2016` or `<22.05.2015 12:00`

Exact date/time attributes looks like `date` or `date time`, i.e. 22.05.2015 12:00 or 12.04.2016

Periodic tasks are specified by attribute starting with `+` : `+[day spec] timespec`, i.e. `+monday friday 02:00` means task occuring each Monday and Friday at 2 am. 

The main purpose of Keeper is to tell if we have enough time for our tasks. After deadlines specified, we might issue following command to see if everything ok:

    keeper check
    
or just

    keeper

It'll show you something like that:

    42 days, 0:00:00  time scheduled
    92 days, 11:00:00  unscheduled worktime left
    All other tasks are 8 days, 4:30:00
    2022.5 h of unassigned time
    NOMINAL
    

which means you have enough time at your hands.

If we add some undoable task, it'll warn us

    FUCKUP <main> None undoable [1000h, <22.10.2015] [1000.0h]
    FUCKUP <main> big projects [998h, <1.1.2016] science work [998.0h]
    83 days, 16:00:00  time scheduled
    50 days, 19:00:00  unscheduled worktime left
    All other tasks are 8 days, 4:30:00
    1022.5 h of unassigned time

# TODO file example

    // this is a comment
    # this is a comment too
    # This is a task. It could be started any time and is 2 hour long
    do a workplan for my project 2h
    
    # this task lasts for 20 minutes and has a deadline of May 23rd 2015
    deploy the first version [<23.05.2015, 20m]
    
    # this is an appointment, which starts on May 24 2014 at 2 pm and will last for 2 hours
    meet the customer [24.05.2015 14:00, 2h]
    
    /*
    This is a multiline comment
    
    You could group tasks into "topics" like that:
    */
    
    planning:
        task 1
        task 2
    work:
        task 3
        task 4
    
    // there are _special_ topics, which aren't taken into accout when _keeper_ is evaluating your time
    // There topics are: done, debts, optional, delegated
    // However, tasks from there topics still could be listed through _keeper list <topic>_ command
    
    done:
        try to get a video from VC hardware
        
    // One can also specify a periodic task like sleep or regular plan meeting
    sleep [+23:00, 8h]
    # each monday and friday, at 10 am , 2 hours long each time
    planning [+monday friday 10:00, 2h]
    
    // everything not recognized between [ and ] becomes additional _topics_ of a task, or _tags_
    // for example, one can mark task as done via additional attribute, instead of putting it into DONE topic
    fix encoding bug for windows version [done]
    
    // Here is an example of extensibility
    // There is a "number of pages" attribute, which was introduced for planning to read a book. If task
    // has an attribute in a form <int>p , then this is interpreted as a page count and this task is also assigned a "books"
    // tag. There are two kind of books - simple and hard. Simple takes 6 minutes per page and _hard_ takes 12
    read Tom Sawyer [200p]
    read Differential Equations by Elsgolts [122p, hard, math, learning]
    
    
    /* One could use following commands to find one or both of these tasks
     * keeper list hard
     * keeper list math
     * keeper list learning
    
      _keeper current_ query evaluates to _keeper list current_ , thus things you want to do first could be marked by
     [current] tag or placed into a current: topic.
     Filenames are topics too, by the way
    */

