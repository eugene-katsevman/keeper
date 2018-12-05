# Keeper
*Keeper* is an extensible console tool for time budgeting and long-term planning.

Keeper's main purpose is to tell if you have enough time.

+[![Join the chat at https://gitter.im/eugene-katsevman/keeper](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/eugene-katsevman/keeper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Short example

Given the following `.todo` file
    
    some tasks [today]:
        buy milk
        do all the work 20h
        so some more work 10h

issuing `keeper check` will give use the following result:

    Assigned time (how long limited tasks will take):  31.0
    Balance (time total balance for limited tasks):    -22.91
    Unbound time (how long free tasks will take):      0.0
    Free time left till latest limited task:           -22.91
    You're short of time. Either limit some unbound tasks, or postpone some of limited
     
    RISKY <main> [some tasks] do all the work 20h [20.0h]

# Contents

- [Install](#install)
- [Introduction](#introduction)
- [Setting up](#layout)
- [Usage](#usage)
- [Attributes](#attributes)
- [Grouping and queries](#grouping-and-queries)
- [Planning and scheduling](#planning)
- [CLI command list](#cli)
- [TODO files format overview](#todo-format)


# Introduction 

Once upon a time I was overwhelmed by tasks. I did not took planning seriously
those days, so it was like a complete disaster. Then I started to use
todo-lists and try to plan my day.

Later I've noticed that all those todo-list application I was using were lacking
one function I was in need for. Although one could set a deadline for every task,
those tools could not tell if there is enough time left to finish those tasks in time.

As a result, this instrument was created.

And I know about `org-mode`, I know it is good at what it does, but I just like
my own solution better:)

# Install

*Keeper* supports only Linux-based OSs with Python 2.7 or 3.3+
You may try to run in under Cygwin or MSYS, but I have never tried it myself.

To install it system-wide simply run the following command:

```
   sudo pip install git+https://github.com/eugene-katsevman/keeper.git
```

After you install it, just run `keeper` to let it create all the needed files
and folders.

Now you're all set and ready to go!

# Directory layout and setting up

On its first run *keeper* will create `.keeper` folder in your home dir.
All `.todo`-files will be stored there.

Also, you can create `.keeperrc` file to alter some settings. `.keeperrc` is a mere python file and can contain following variables:

* `EDITOR` - preferred editor, like `vim`. EDITOR is set to 'auto' by default, which makes keeper try several popular editors
* `POSSIBLE_EDITORS` - which editors to try in `EDITOR='auto'` mode
* `IGNORED_SECTIONS` - this is a set of _topics_, which are not listed or processed by default, e.g. 'done', 'wontdo' or 'optional'.
* `SYNONYMS` - this is a tag synonyms mapping
* `HARD_PAGE_TIME`, `EASY_PAGE_TIME` - how much time in hours takes one page of a book. This is used to plan your reading.

#  Usage
To start using *keeper* just run

```bash
keeper edit main
```

Keeper will open an editor session for `~.keeper/main.todo` file. 

`*.todo` files are task specification files.
To see how this works, put the following  line into the `main.todo` and then save it.

    My first task

Now run `keeper list`. The response should be something like that:

    <main> None My first task [1h]
    Total: 1 task(s), 1 h of worktime

`<main>` is a filename, where our first task is stored.

Tasks are 1 hour long by default. This happens to be a very sane assumption.

Now add one more task:

    My first task
    My second task 2h

and run `keeper list` again:

    <main> None My first task [1h]
    <main> None My second task 2h [2h]
    Total: 2 task(s), 3 h of worktime

Everything that looks like integer with _h_ or _m_ at the end is captured as task duration.

# Attributes
Each task may have different attributes. Task duration is only one of them.
There could be **deadlines** , **exact start time**, **periodics** specification, **tags** and some other kinds of attributes.

Attributes are listed in square brackets at any part of task and should be comma-separated from each other.
Let us add attributes to our tasks:

    My first task
    My second task 2h [must, <22.10.2015]

Second task now has three attributes: 2h duration, `must` tag and a deadline.

Any attribute not recognised as special (like _deadline_ or _periodics_, or duration)
is assumed to be a _tag name_. _Topics_ actually are tags too.
So to query for `must` tasks we should issue then next command:

    keeper list must

`*.todo` file names are tags too. Command `keeper list asdf` will return all tasks from asdf.todo along with all tasks from topic `asdf` and all other tasks marked by `asdf` tag (like **[asdf]**).

If attribute is set for a topic, this exact attribute is automatically set for all topic's tasks

Keeper supports the following attributes:

*duration*     is specified as Xh|Ym like 2h or 30m. You've seen an example above.

*start time*   is used for meetings or other appointed tasks. The format is HH:MM dd.mm.yyyy

*deadline*     follows the format <[HH:MM] dd.mm.yyyy. You can omit time for a deadline.

*periodics*    is for specifying periodically occuring time sinks like sleep or eating.
The format is +[weekday, [weekday2...]] [HH:MM]. I.e. `sleep [+23:00, 8h]` means you sleep every day from 23:00 till 7:00 next day and `gym  [+monday tuesday 8:00]` means you go to gym two days per week at 8am for one hour

*page count*   is used for adding tasks for reading books. `120p` means that book has 120 pages. This value is used to calculate the task duration.

*hard*         this is a modifier for books. 
             
*spent*        spent [Xh] like `spent 20h`

*today*        this is a shortcut for the next day deadline

*done*         this taks is done and will not be shown or accounted for unless explicitly queried.

*wontdo*       works line *done*, but has a slightly different meaning. You are not going to finish it.

*delegated*, *optional*, *debts*, *library*, *scratch*, *optional*, *paid*, *ext*, *passwords*  These are ignored attributes. Tasks with those attributed will not show up or be accounted unless specifically queried for, like `done` and `wontdo`.

# Grouping and queries
The `keeper list` command keeps showing us `None` after the task filename. `None` means our tasks do not belong to any _topic_. Let us fix that now:

    My first task
    My second task 2h
    project1:
        My third task 40m
        My fourth task 4h
    
We just have grouped third and fourth task in a *project1* topic.

`keeper list` will give us the following:

    <main> None My first task [1h]
    <main> None My second task 2h [2h]
    <main> project1 My third task 40m [0.67h]
    <main> project1 My fourth task 4h [4h]
    Total: 4 task(s), 7.67 h of worktime

If you want to list only `project1`'s tasks, you can do that by:

    keeper list project1

To list all tasks, simultaneously having several taks, we should provide a dot-separated list of these tags to `keeper list`:

    keeper list main.must

OR queries are done by providing space-separated list of tags to `keeper list`

This command will seek for all done tasks or delegated to alex
    
    keeper list done delegated.alex
    

# Planning and scheduling

Till now we were setting deadlines, durations and other attributes, but how this corresponds to planning?
The main goal of keeper is to evaluate you time budget and you can do that by issuing the following command:

    keeper check

or just

    keeper

Keeper will go through all todo files, accumulate all tasks and tell you if everything is okay.
If this is not the case, keeper will tell you which tasks are jeopardized.
This is the whole point.

# CLI command reference

```keeper check```

Quick check current scheduled tasks. This is the default command. If you run `keeper` with no arguments, it will be invoked.

```
  keeper list [tag1[.tag2[...]] [tag3...]
```

List tasks. Use `.` for AND query and space (` `) for OR query.

```  
  keeper show_topics
```

List all available topics (tags).
  
```
  keeper edit [filename [filename2...]]
```

Open specified .todo files for editing or open all available files, if no filename was provided.

```  
  keeper today
```

List all tasks to be done today.

```
  keeper random
```

Gives you 10 random tasks to do. This is for undecisive procrastinators, like myself.

```
  keeper scheduled
```

List all scheduled tasks.

```
keeper done <filename> [<filename2> ...]
```

Rename [filename].todo to [filename].done. This excludes _filename_ from processing. A quick hack, yep.

```
  keeper undo <filename> [<filename2> ...]
```

Rename [filename].done back to [filename].todo

# TODO files format overview

The following is an example of `.todo` file. These files are written as a plain text
with a little bit of special formatting, which will be explained in the nex section.

    // this is a comment
    # this is a comment too
    # This is a task. It could be started any time and is 2 hour long
    do a workplan for my project 2h
    
    # this task lasts for 20 minutes and has a deadline of May 23rd 2015
    deploy the first version [<23.05.2015, 20m]
    
    # this is an appointment, which starts on May 24 2015 at 2 pm and will last for 2 hours
    meet the customer [24.05.2015 14:00, 2h]
    
    /*
    This is a multiline comment
    
    You can group tasks into "topics" like that:
    */
    
    planning:
        task 1
        task 2

    work:
        task 3
        task 4
    
    // There are _special_ topics, which aren't taken into accout when _keeper_ is evaluating your time
    // These topics are: done, debts, optional, delegated and some other
    // However, tasks from these topics still could be listed through _keeper list <topic>_ command
    
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

