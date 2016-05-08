# Fruitpile
Fruitpile is intended to be an artifact management system like
Artifactory or Nexus. 

*Note this document is rather more aspirational than factual at the
moment - do not expect Fruitpile to do everything listed here yet.*

## Travis Status
[![Build Status](https://travis-ci.org/software-fool/fruitpile.svg?branch=master)](https://travis-ci.org/software-fool/fruitpile)

# What is Fruitpile

Fruitpile is intended to be an artifact management system like
Artifactory or Nexus.  However, Fruitpile has been written to address
the needs that I have for managing binaries through our build system.

Specific things that Fruitpile has been engineered to do are:

* Allow artifacts to travel through a series of states
* Allow arbitrary tags and properties to be added to the files
* Allow artifacts to be grouped (for example all the build outputs
  from a given build as might be the case for cross platform building)
* Allow those grouped files to be managed both independently or
  together
* Allow additional files to attached to the main artifacts as
  supporting evidence, for example test reports (the test reports in
  turn can be required to be present for state transitions)
* Allow relatively straightforward integration into other environments
* Allow a rich set of permissions to allow each operation to be
  largely independently controlled
* Integrate to an LDAP directory and use it for authentication
* Be small and yet fast

Specific things that Fruitpile has not been engineered to do (but
which may be possible)

* Understand repositories of any particular kind (e.g. Maven, PyPi,
  RPM, APT for example)
* Necessarily understand the files content
* Directly provide a web interface.
* Make money from it
* Provide multiple different authenication systems (or even its own)

There may be other things as well, but having investigated Artifactory
and Nexus sufficiently far to find out they do not really meet my
needs I did not investigate further.

Further discussion on these topics is below providing some information
on my use case which may help to understand the design decisions I
have made.

### Why Fruitpile

The name Fruitpile comes from the notion that the artifacts are the
_fruits_ of our labours and a _pile_ is simply a heap collection of
things.  Essentially a heap of stuff which seems pretty apposite.

## States

In my use case what was needed was the ability to take builds directly
from a CI system and post them to a store.  Then once manual and
stability and other forms of performance testing have been completed
enable the artifacts to be moved to release.  Releases also needed to
be able to be withdrawn.

Therefore the idea of a state attached to each item makes sense.
Items move through the different states according to where they are in
the cycle.  Also some states cannot be reached from others
(e.g. released cannot be reached directly from untested.)
Additionally some states can require additional supporting evidence to
be present and attached to the item in order to transition its state
(see discussion of additional files below)

State transitions are controlled by permissions too so that it's
possible to use Fruitpile to manage who can change what and under what
conditions.

## Tags (or Labels) and Properties

As far as Fruitpile is concerned tags and labels are the same thing -
simple _words_ that are attached to an artifact.  This allows not
hierarchical groups to be established.

Fruitpile itself imposes a hierarchical structure internally (it
stores files on the filesystem so a hierachical structure is
inevitable) but tags allow the strata across the data to be
established in useful ways.  For example the ability to look at all
the ARM Cortex-M4 builds might be an interesting way at looking at the
data and allows people to find the files they want rather quicker.

However labels are really just a special case of properties, but are
distinct because tags are so useful in their own right.  The
distinction is essentially that properties are key-value pairs while
tags are in essence key-value pairs where the key is "tag".  There is
one other important difference however.  An artifact can have any
number of associated properties but the keys must be unique.

## Grouping

Fruitpile allows grouping via file sets.  In my use case a file set is
a set of artifacts produced by a single build which would be target
binaries for several different targets.  By grouping files like this
it allows some data to be associated with the fileset.  For example,
in our case the build is essentially comprised of two pieces: some
binaries for a variety of platforms and some data that those binaries
use.  Because the data component is tested extensively independently
before being combined with the binaries for release the tests
conducted prior to release are related to the fileset not the
artifact.  (See auxilliary files below.)

Grouping allows this data to be associated with all the artifacts in a
build simultaneously and also allows the whole group of files to be
transitioned through states simulaneously.  Artifacts can be state
controlled independently or through file sets. Of course there can be
a single fileset for all files or a fileset per file and anything in
between so the file set grouping is entirely optional.

## Auxilliary Files

Auxailliary files are additional files that are not controlled
themselves but are used to provide additional support to the
transition of an artifact which is controlled.  Examples are test
reports and release notes which are not artifacts that are necessary
controlled in their own right but are part of the the file set that
gets transitioned through the state model.

Auxilliary files can be required for certain state transitions (as
test reports and release notes would be) but they don't need to be.
In almost every other respect they are processed identically to the
controlled artifacts.

## Licensing

Fruitpile is licensed under the version 3 of the
[GPL](http://www.gnu.org/licenses) which is good for Fruitpile since it means
no-one can ever further restrict its use.  However, it might create
issues for someone wanting to integration commercial software around
it.  For this reason Fruitpile has been designed to allow a commercial
front-end or integration with commercial producs through the REST API
without GPL contamination concerns.  (I'm not a lawyer though and so
integrators should certify for themselves that they are happy with
this position.) 

## Flexible Integration Options

Fruitpile is initially a command line tool that allows the Fruitpile
operations to be carried out.  However the command line tool is
actually a thin wrapper around the Fruitpile core API.  The API itself
has a RESTful interface that is managed through
[Flask](http://flask.pocoo.org/).  Since Flask is a web platform
designed for supported full scale web sites, the RESTful API is not a
toy implementation - it's designed for operation at scale.  Fruitpile
follows in this mentality.

As indicated above there's no UI provided with Fruitpile by design.
There are two reasons for this:

1. I'm not a UI designer or a web front end developer and while I can,
I'm not good at it.  The world will be a better place if someone more
competent to do this does it.
2. Providing a RESTful API permits the option for commercial front
ends or integration with other tools, including other artifact
managers.

In practice, it is expected that the REST API will be the way that
Fruitpile is deployed and, rather like [AWS](http://aws.amazon.com/),
it is intended that all (or very nearly all) the operations of
Fruitpile are accessible through the REST API.

## Rich Permissioning

In early versions there's no permissions checking but the intention is
to provide hooks into the permissions framework from pretty much every
point.  With lots of permissions comes complexity however, and
Fruitpile comes with a reasonable set of preconfigured groups which
should meet more common usages.  However, it's possible to control the
permissions given to a group or an individual to quite a fine level.
(The permissioning system is expected to appear soon but not actually
validate anything.)

## Integration with LDAP Directories

Fruitpile is not intended to provide authentication services itself
but rather piggy back on other systems.  The most obvious for
Fruitpile would be Unix users and groups but for my purposes the main
use case is within an Active Directory environment.  Thus LDAP
integration seems the most obvious choice.  Since LDAP integration is
pretty straightforward from Python this makes it the obvious choice
for the Fruitpile.

## Small and Fast

One objection I had to Artifactory and to Nexus is that the packages
to download were nearly 40M and then there's the JVM to download
alongside.  Development teams tend to rally around tools they know.
I'm sure Artifactory and Nexus make perfect sense if you are Java
house but we're not and loading the JVM onto all those extra machines
is just overhead.  Now that Oracle has taken over Java it's also
harder to get older versions when Oracle decides that it's time-up it
requires a mass upgrade.

Python is a big part of what I do and so hooking into that knowledge
is less of a steep curve.  Not having to deal with properties files
and XML (a firm favourite of Java programmers) is also a problem as it
doesn't merge easily so managing configuration is harder.

# To do

## States

* add comments to state transition
* add functions to allow extra conditions to be checked when
  transitioning stats
  (Apr-2016: one function added to check for the existence of another
  auxilliary file)

## Operations

* (Apt-2016: done) get file
* move file (locations)
* archive files
* change file type (auxilliary->primary/primary->auxilliary)

## Tags and Properties

* (Apr-2016: done) Tags and properties enabled for FileSets
* (Apr-2016: done) Tags and properties on binfiles

## command line tool

* provide a simple daemon backend to start fruitpile and then a
  fruitend tool to modify it (might as well use the RESTful API
  though)

## REST API

* (Apr-2016: done) Ability to list files and filesets as well as ability to
  create a fileset.
* (Apr-2016: done) Add filesets
* Add files
* Search

## Load test

* Is it possible to use Fruitpile to manage large numbers of files
  (say hundreds of thousands or millions?)

## Maintenance

* Backup
* Upgrade (Apr-2016) began the first part of this by providing at
  least the outline of how an upgrade might work.  Something like
  the upgrade/downgrade script components are subsumed into the
  store so they can be found later - rather like the way Windows apps
  bury their installers into the Windows directory somewhere


