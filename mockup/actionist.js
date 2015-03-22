var ToDoForm = React.createClass({
    getInitialState: function () {
        return {
            showOptions: false,
            showSchedule: false,
        };
    },

    componentDidMount: function () {
        document.addEventListener("click", this.hideOptions);
        // Check the default option for Later in a way that bypasses making it
        // a controlled component.
        //
        // http://stackoverflow.com/q/28298163/1070621
        this.getDOMNode().querySelector("#new-to-do-later").checked = "checked";
    },

    hideOptions: function (e) {
        // Hide new to-do form if user clicks anywhere other than the form
        // or individual to-do items.
        var newToDoForm = $("#new-to-do-form");
        var workspace = newToDoForm.add("#to-do-list");
        if (!workspace.is(e.target) &&
            workspace.has(e.target).length === 0 &&
            this.state.showOptions)
        {
            this.setState({showOptions: false});
        }
    },

    showOptions: function (e) {
        if (!this.state.showOptions)
            this.setState({showOptions: true});
    },

    toggleSchedule: function (e) {
        this.setState(function (previousState, currentProps) {
            return {showSchedule: !previousState.showSchedule};
        });
    },

    render: function () {
        var optionsFieldSetStyle = {
            display: (this.state.showOptions ? "block" : "none")
        };

        var scheduleFieldSetStyle = {
            display: (this.state.showOptions && this.state.showSchedule ? "block" : "none")
        }

        return (
            <section>
            <form id="new-to-do-form" method="POST">
                <div id="new-to-do-title" className="text-field field">
                    <input name="title" type="text" placeholder="What will you do?" onFocus={this.showOptions} />
                    <input type="submit" value="Add" />
                </div>
                <div id="new-to-do-options" className="field-set" style={optionsFieldSetStyle}>
                    <div className="radio-field field">
                        <input id="new-to-do-later" name="current" type="radio" value="0" />
                        <label htmlFor="new-to-do-later" className="to-do-later to-do-option">Later</label>
                    </div>
                    <div className="radio-field field">
                        <input id="new-to-do-today" name="current" type="radio" value="1" />
                        <label htmlFor="new-to-do-today" className="to-do-today to-do-option">Today</label>
                    </div>
                    <div className="divider"></div>
                    <div className="checkbox-field field">
                        <input id="new-to-do-repeat" name="repeat" type="checkbox" />
                        <label htmlFor="new-to-do-repeat" className="to-do-repeatable to-do-option">Repeat</label>
                    </div>
                    <div className="divider"></div>
                    <div className={"schedule" + (this.state.showSchedule ? " selected" : "")} onClick={this.toggleSchedule}>
                        <a href="#">Schedule...</a>
                    </div>
                </div>
                <div id="new-to-do-schedule" className="field-set" style={scheduleFieldSetStyle}>
                    <div className="datetime-field field">
                        <label htmlFor="new-to-do-date">When</label>
                        <input id="new-to-do-date" name="date" type="date" placeholder="Date" />
                        <input id="new-to-do-time" name="time" type="time" placeholder="Time?" />
                    </div>
                </div>
            </form>
            </section>
        );
    }
});

var ToDoList = React.createClass({
    getInitialState : function () {
        return {
            data: [
                {
                    id: 1,
                    title: "Work out",
                    dateTime: {},
                    done: false,
                    current: true,
                    repeatable: true
                },
                {
                    id: 2,
                    title: "Doctor's appointment",
                    dateTime: {
                        date: "02/14/2014"
                    },
                    done: false,
                    current: false,
                    repeatable: false
                },
                {
                    id: 3,
                    title: "Task 3 With A Super Long Name Like This One Blahblahblah Some Superduperlong Words And Then Some This Title Is Long",
                    dateTime: {
                        date: "03/21/2015",
                        time: "3:42pm"
                    },
                    done: false,
                    current: true,
                    repeatable: true
                },
                {
                    id: 4,
                    title: "Practice guitar",
                    dateTime: {},
                    done: false,
                    current: true,
                    repeatable: true
                }
            ]
        };
    },

    render: function () {
        var toDoItems = this.state.data.map(function (toDoItem) {
            return (
                <ToDoItem id={toDoItem.id}
                          title={toDoItem.title}
                          dateTime={toDoItem.dateTime}
                          done={toDoItem.done}
                          current={toDoItem.current}
                          repeatable={toDoItem.repeatable}>
                </ToDoItem>
            );
        });

        if (toDoItems.length)
            return (<section id="to-do-list">{toDoItems}</section>);
        else
            return (<p className="empty">Nothing to do. Yet. :)</p>);
    }
});

var ToDoItem = React.createClass({
    getInitialState: function () {
        return {
            expanded: false
        };
    },

    expand: function (e) {
        e.preventDefault();
        this.setState(function (previousState, currentProps) {
            return {expanded: !previousState.expanded};
        });
    },

    editTitle: function () {
        var titleLabel = $(todo.children(".to-do-title")[0]);
        var titleText = $(titleLabel.children("a")[0]);
        var editTitle = $("<input />", {
            class: "to-do-title-edit",
            type: "text",
            value: titleText.text()
        });
        todo.addClass("expanded");
        titleLabel.append(editTitle);
        titleText.hide();
        editTitle.focus();
    },

    render: function () {
        var dateTimeDetail;
        if ("date" in this.props.dateTime)
        {
            var dateTimeString = this.props.dateTime.date;
            if ("time" in this.props.dateTime)
            {
                dateTimeString += " @ " + this.props.dateTime.time;
            }
            dateTimeDetail = <div className="to-do-detail to-do-datetime">{dateTimeString}</div>
        }


        return (
            <div className={"to-do" + (this.state.expanded ? " expanded" : "")}>
                <input id={"checkbox-" + this.props.id} type="checkbox" />
                <label className="to-do-checkbox" htmlFor={"checkbox-" + this.props.id}></label>
                <label className="to-do-title">
                    <a href="#" title={this.props.title} onClick={this.expand}>{this.props.title}</a>
                </label>
                <div className="to-do-info">
                    <div className={"to-do-detail " + (this.props.current ? "to-do-today" : "to-do-later")}></div>
                    {this.props.repeatable ? <div className="to-do-repeatable to-do-detail"></div> : null}
                    {dateTimeDetail}
                </div>
                <ToDoActions />
            </div>
        );
    }
});

var ToDoActions = React.createClass({
    getInitialState: function () {
        return {
            activeOption: null,
        };
    },

    activateOption: function (optionType) {
        this.setState(function (previousState, currentProps) {
            if (previousState.activeOption === optionType)
                return {activeOption: null};
            else
                return {activeOption: optionType};
        });
    },

    cancelChoice: function () {
        this.setState({activeOption: null});
    },

    confirmChoice: function () {
    },

    render: function () {
        if (this.state.activeOption === null)
        {
            return (
                <div className="to-do-actions">
                    <ToDoOption type={this.props.current ? ToDoOption.Type.Later : ToDoOption.Type.Today} onActivate={this.activateOption} />
                    <ToDoOption type={ToDoOption.Type.Edit} onActivate={this.activateOption} />
                    <ToDoOption type={ToDoOption.Type.Delete} onActivate={this.activateOption} />
                </div>
            );
        }
        else
        {
            switch (this.state.activeOption)
            {
                case ToDoOption.Type.Today:
                    actionPrompt = "Do this today?";
                    break;
                case ToDoOption.Type.Later:
                    actionPrompt = "Do this later?";
                    break;
                case ToDoOption.Type.Edit:
                    actionPrompt = "Making changes.";
                    break;
                case ToDoOption.Type.Delete:
                    actionPrompt = "Discard forever?";
                    break;
                default:
                    console.error("ToDoOption.actionPrompt got invalid type: " + this.state.activeOption);
                    actionPrompt = "";
            }
            var changePrompt = (
                <div className="to-do-change">
                    <p>{actionPrompt}</p>
                    <a className="yes" href="#" onClick={this.confirmChoice}>
                        {this.state.activeOption === ToDoOption.Type.Edit ? "Save" : "Yes"}
                    </a>
                    <a className="no" href="#" onClick={this.cancelChoice}>
                        {this.state.activeOption === ToDoOption.Type.Edit ? "Cancel" : "No"}
                    </a>
                </div>
            );

            return (
                <div className="to-do-actions selected">
                    <ToDoOption type={this.state.activeOption} onActivate={this.activateOption} />
                    {changePrompt}
                </div>
            );
        }
    }
});

var ToDoOption = React.createClass({
    typeClassName: function () {
        switch (this.props.type)
        {
            case ToDoOption.Type.Today:
                return "to-do-today";
            case ToDoOption.Type.Later:
                return "to-do-later";
            case ToDoOption.Type.Edit:
                return "to-do-edit";
            case ToDoOption.Type.Delete:
                return "to-do-delete";
            default:
                console.error("ToDoOption.typeClassName got invalid type: " + this.props.type);
                return "";
        }
    },

    activate: function () {
        this.props.onActivate(this.props.type);
    },

    render: function () {
        return (
            <a className={"to-do-option " + this.typeClassName()} href="#" onClick={this.activate}></a>
        );
    }
});

ToDoOption.Type =  {
    Today: 0,
    Later: 1,
    Edit: 2,
    Delete: 3
};

React.render(
    <div className="panel">
    <header><h2>Actionist</h2></header>
    <ToDoForm />
    <ToDoList />
    </div>,
    document.getElementById("content")
);
