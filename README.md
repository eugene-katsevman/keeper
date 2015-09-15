
# keeper
console time manager

+[![Join the chat at https://gitter.im/eugene-katsevman/keeper](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/eugene-katsevman/keeper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
 console time manager


An extensible console tool for long-term planning.

Here is an example of todo file
<pre>
// this is a comment
# this is a comment too
# This is a task. It could be started any time and is 2 hour long
do a workplan for my project 2h

# this task lasts for 20 minutes and has a deadline of May 23rd 2015
отправить первую версию программы [<23.05.2015, 20m]

# this is an appointment, which starts on May 24 2014 at 2 pm and will last for 2 hours
встретиться с заказчиком [24.05.2015 14:00, 2h]

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
</pre>
