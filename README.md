QEMS2 - a question submission and editing system
=====

## What is it?

QEMS2 is a successor to a system called, intuitively enough, QEMS, which was used by [High School Academic Pyramidal Questions](http://www.hsapq.com) to produce quizbowl questions for various high school quizbowl competitions. The original QEMS was written in PHP and broke down after the maintainer stopped working on it; it was also completely hand-coded and made no use of modern web development frameworks or standards. QEMS2 is an attempt to remedy all that, by rebuilding the system from the ground up using modern tools.

## Stack

QEMS2 is based on a technology stack that uses MySQL for storage, Python (in the form of Django) for the backend, and jQuery/Bootstrap for frontend manipulations. 

## Installation

Grab the code:

    git clone https://github.com/grapesmoker/qems2

Because the Django secret key is not checked in, you will need to create a new file called "secret" in the root directory that you cloned.  This file will look something like this:

    SECRET_KEY = 'your secret key'

### Generic *nix (including OS X)

To run QEMS2, you'll need the following prerequisites.

    python2 >= 2.7, MySQL, nodejs

Once you have those installed, you should use `pip` to get the necessary Python packages

    sudo pip install django
    sudo pip install beautifulsoup4
    sudo pip install django-bower
    sudo pip install django-contrib-comments
    sudo pip install django-haystack
    sudo pip install whoosh
    sudo pip install mysql-python
    sudo pip install unicodecsv

It's generally recommended that you use `virtualenv` to set up a virtual environment for your project. 

Next, grab `bower` using `npm` for front-end package management:

    sudo npm install -g bower

Set up your MySQL connection as, for example, `mysql -u root -p`:

    CREATE USER django@localhost IDENTIFIED BY 'django';
    CREATE DATABASE qems2_stable;
    GRANT ALL PRIVILEGES ON qems2_stable.* TO django@localhost;
    GRANT ALL PRIVILEGES ON test_qems2.* TO django@localhost;

Finally, use `manage.py` to populate the database, install the front-end packages, collect static files, and start the development server:

    python manage.py syncdb
    python manage.py bower install
    python manage.py collectstatic
    python manage.py runserver

If the bower install command is failing because node can't be found, you may need to install nodejs-legacy.

### Windows

Install the 32-bit version of Python 2.7.9 to C:\Python27; make sure to install the component that modifies your path. If the msi fails due to a missing DLL component, navigate to C:\Users\{username}\AppData\Local, right-click on Temp, go to Properties > Security and give "Everyone" "Full Control" (you'll get a lot of errors, just power through w/ the okay button).

Install the 32-bit MySQL installer from http://dev.mysql.com/downloads/windows/ and the 32-bit msi from http://nodejs.org/download/.

Run an instance of Windows PowerShell as an administrator and:

    pip install django
    pip install beautifulsoup4
    pip install django-bower
    pip install django-contrib-comments
    pip install django-haystack
    pip install whoosh
    pip install unicodecsv

Install the latest from https://pypi.python.org/pypi/MySQL-python/, make sure git is installed, and make sure all of the above programs are in your path, incl. variations on: C:\Program Files (x86)\MySQL\MySQL Workbench 6.2 CE\, C:\Program Files (x86)\Git\cmd\, C:\Python27\, C:\Python27\Scripts\, C:\Program Files (x86)\nodejs\, C:\Users\Andrew\AppData\Roaming\npm\. Then npm install -g bower.

Then follow the above instructions to set up the MySQL connection and the server, except make sure to add `BOWER_PATH = os.path.normpath(r'C:\Users\{username}\AppData\Roaming\npm\bower.cmd')` below the `BOWER_COMPONENTS_ROOT` line in settings.py before `bower install`'ing. Note that the installation of git may require you to reference python as `C:\Python27\python.exe` instead of `python` in PowerShell.

### Running QEMS2

As with any Django project, you should now be able to access the website at http://localhost:8000.

If you have created a user 'admin2', you can populate the database with some default data by running `python manage.py shell < qems2/qsub/populate_db_with_default_data.py`.

## Usage

QEMS2 is currently in heavy development. Although the core parts of the application are stable, features are being added all the time, so it's hard to give an exhaustive description of them all here. The foregoing will summarize the basic concepts involved in the question submission and editing workflow.

### Roles

QEMS2 is structured around the concept of roles. There are three types of roles in the system: owners, editors, and writers (there are also administrators who can access the admin site, but that is not strictly speaking a part of the application itself). The hierarchy of powers is strictly inclusive from the top down, i.e. anything that an editor can do, an owner can do, and anything that a writer can do, an editor can do.

1. Owners: Anyone who creates a tournament is automatically the owner of that tournament and has complete freedom to do anything they would like to it. This includes assigning other users to be editors or writers of their tournament, modifying the tournament distribution, and editing any question in the system.
2. Editors: these users have the power to edit or delete any question in the system. They do not have the power to change the distribution or the core information about the set. Editors can also lock questions to prevent writers from editing those questions.
3. Writers: these users are empowered only to submit questions, edit (unlocked) questions that they have submitted, and see (but not edit) questions submitted by others.

In addition, any user can leave comments on packets, individual questions, or the set as a whole.

### Distributions

The number and type of questions that a question set requires is controlled by assigning a distribution to a set. You can create a distribution by clicking on the `Distributions` link on the sidebar, giving your distribution a name, and adding category/subcategory entries, in addition to numbers specifying both maximum and minimum tossups and bonuses in that category _per packet_.

### Question Sets

The question set is the basic unit of operation in QEMS2. Question sets are created by clicking on the `Question Sets` link on the sidebar and then `Create Question Set`. Question sets are required to have _some_ distribution, but picking a distribution does not preclude you from editing that distribution later. Once a question set is created, you can manage that question set through various tabs:

- Question set info: this tab contains the basic information about the set (name, date, and distribution), as well as a status report on the set's completion. The status screen lets you know how many questions of each kind have been written and how many still remain to be written. Green check marks indicate that the minimum number of questions in each category/subcategory entry have been written.
- Editor assignments: this tab allows the owner to add writers and editors to a set. Clicking on either `Add Editor` or `Add Writer` brings up a screen with a list of users who can be added to the set. Users can only be either writers or editors.
- Set-wide distribution: this is one of the most important tabs. The set-wide distribution controls the _total_ number of questions in each category/subcategory entry. You cannot change the categories themselves (that is only possible via the `Distributions` screen); you can only change the _total_ number of tossups and bonuses in each. This number covers the _entire set_ as opposed to the main distribution which applies at the packet level. For example, the a distribution may call for a maximum of 1 tossup and 1 bonus and a minimum of 0 of each in the category/subcategory `Science/Math`. Those constraints apply on a _per packet_ basis. If you have 10 packets in your set, you may only want 5 tossups and 5 bonuses in `Science/Math`, in which case you would set the numbers for the set-wide distribution 5 each.
- Tiebreaker distribution: the tiebreaker distribution functions exactly like the set-wide distribution, but only applies to tiebreaker questions. The numbers indicate the _total_ number of tiebreakers in each category/subcategory entry on a _per set_ basis.
- Questions: this tab gives users access to the questions that are part of the set. From here, a user can either add tossups and bonuses to the set manually or by uploading a file. It also shows users the questions that are part of the set. From here, an editor can click on the `Edit` link under the `Actions` column to edit the questions. The editorial workflow will be covered in a different section.
- Packets: questions are collected into packets. This tab allows the owner to create a packet, or multiple packets to be part of the set. Clicking on a packet link will bring up a page that indicates the completion status of the packet, which is similar to the completion status page of the set. The completion status of a packet is controlled by distribution assigned to the set. This tab also allows the owner to add questions either manually or from an existing stock of questions that are part of the set but have not been assigned to a packet.

### Editing Workflow

The editing workflow of QEMS2 starts with writers and editors being assigned to a question set by the set owner. After that, writers and editors are free to start writing questions; they can do so either by adding questions manually or uploading questions in a text file. Once a writer has submitted a question, it can be edited by an editor. Usually, once the editor has completed their editing, they can lock a question from further editing by a writer. This does not prevent the editor or the set owner from editing these questions; it only locks out the original question writer. At any point, a question may be moved by an editor or the set owner into a packet.

The submission/editing cycle continues until both the set-level constraints and the packet-level constraints have been satisfied. Once the constraints have been satisfied and the questions have been assigned to packets, the packets may be exported to PDF form. At that point, the set is ready to be played.

### Format for Question Uploads

If you are uploading questions, they have to be formatted in a certain way. An uploaded file must be in plain text, and the questions must have this form:

##### Tossups:
        
> This scientist noted the difference between Asiatic and Oceanic fauna, hypothesizing that their geographical isolation played a role in their different developments; the boundary between the two types of fauna is now known as his namesake line. For 10 points, identify this scientist who proposed a theory of evolution contemporaneously with Charles Darwin.

> ANSWER: Alfred Russell \_Wallace\_

Note that the question text must be all on a single line, followed by a carriage return, with the answer prefaced by the word `"ANSWER:"` and the required parts of the answer set off by the underscore marks.

##### Bonuses:

> At one point in this film, two characters are arrested after they mistake dust-covered Union soldiers for Confederates. For 10 points each:

> [10] Identify this film in which those two characters later help a Union colonel blow up a bridge across a river that they need to cross, while searching for Bill Carson's gold.

> ANSWER: The \_Good, the Bad, and the Ugly\_

> [10] _The Good, the Bad, and the Ugly_ is probably the most famous of the spaghetti westerns of Sergio Leone, starring this man as "Blondie."

> ANSWER: Clint \_Eastwood\_

> [10] Eastwood's other quasi-historical roles include this role in _Unforgiven_, in which he kills the Sherrif played by Gene Hackman, as revenge for Hackman's killing of his companion, played by Morgan Freeman.

> ANSWER: \_William\_ [or \_Bill\_] \_Munny\_ [accept either name]

The leadin must be on a single line, followed by a newline. Each part must be prefaced with the value in square brackets, e.g. `[10]`, followed by the text of the bonus part, followed by a newline. As with tossups, the answer must be set off with `"ANSWER:"` followed by the answer. In the prompt, emphasis can be applied using underscores (or asterisks), while in the answer, underscores are used to indicate required parts. You do not need blank lines between question parts and answers; those are just here for readability and will be ignored.

## Testing

To run the included unit tests (under `qems2/qsub/tests/`):

    python manage.py test qems2/qsub/tests/

If a test fails, that is probably a bad thing.

## Upcoming Features

QEMS2 is evolving fairly rapidly. Features are being added frequently at the request of the users. There are a number of upcoming additions that will be made to QEMS2 in the next few months:

1. Bulk question writing will allow users to write directly into a text-box instead of having to upload a file.
2. Question set status that takes tiebreakers into account.
3. Customizable PDF generation.
4. Pagination in long lists
5. Full-text search
