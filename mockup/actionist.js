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
            data: {
                1: {
                    id: 1,
                    title: "Work out",
                    dateTime: {},
                    done: false,
                    current: true,
                    repeatable: true
                },
                2: {
                    id: 2,
                    title: "Doctor's appointment",
                    dateTime: {
                        date: "02/14/2014"
                    },
                    done: false,
                    current: false,
                    repeatable: false
                },
                3: {
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
                4: {
                    id: 4,
                    title: "Practice guitar",
                    dateTime: {},
                    done: false,
                    current: true,
                    repeatable: true
                }
            }
        };
    },

    deleteItem: function (id) {
        this.state.data[id] = null;
        this.setState({data: this.state.data});
    },

    render: function () {
        var that = this;
        var toDoItems = Object.keys(this.state.data).map(function (id) {
            var toDoItem = that.state.data[id];
            if (toDoItem)
            {
                return (
                    <ToDoItem
                        id={toDoItem.id}
                        title={toDoItem.title}
                        dateTime={toDoItem.dateTime}
                        done={toDoItem.done}
                        current={toDoItem.current}
                        repeatable={toDoItem.repeatable}
                        onDelete={that.deleteItem}
                    />
                );
            }
        });

        if (toDoItems.length)
            return (<div id="to-do-list">{toDoItems}</div>);
        else
            return (<p className="empty">Nothing to do. Yet. :)</p>);
    }
});

var ToDoItem = React.createClass({
    getInitialState: function () {
        return {
            expanded: false,
            editing: false,
            title: this.props.title,
            done: this.props.done,
            current: this.props.current
        };
    },

    componentDidUpdate: function () {
        if (this.state.editing)
        {
            var titleInput = this.getDOMNode().querySelector(".to-do-title-edit");
            titleInput.focus();
            titleInput.value = this.props.title;
        }
    },

    delete: function () {
        this.props.onDelete(this.props.id);
    },

    expand: function (e) {
        e.preventDefault();
        this.setState(function (previousState, currentProps) {
            return {expanded: !previousState.expanded};
        });
    },

    edit: function (activateEditing) {
        if (activateEditing)
            this.setState({expanded: true, editing: true});
        else
            this.setState({editing: false});
    },

    save: function () {
        var newTitle = React.findDOMNode(this.refs.titleInput).value.trim();
        this.setState({editing: false, title: newTitle});
    },

    toggleCurrent: function () {
        this.setState(function (previousState, currentProps) {
            return {current: !previousState.current};
        });
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

        var title;
        if (this.state.editing)
            title = <input className="to-do-title-edit" type="text" ref="titleInput" />;
        else
            title = <a href="#" title={this.state.title} onClick={this.expand}>{this.state.title}</a>;

        return (
            <div id={"to-do-" + this.props.id} className={"to-do" + (this.state.expanded ? " expanded" : "")}>
                <input id={"to-do-checkbox-" + this.props.id} type="checkbox" checked={this.state.done} />
                <label className="to-do-checkbox" htmlFor={"to-do-checkbox-" + this.props.id}></label>
                <label className="to-do-title">
                    {title}
                </label>
                <div className="to-do-info">
                    <div className={"to-do-detail " + (this.state.current ? "to-do-today" : "to-do-later")}></div>
                    {this.state.repeatable ? <div className="to-do-repeatable to-do-detail"></div> : null}
                    {dateTimeDetail}
                </div>
                <ToDoActions
                    current={this.state.current}
                    onToggleCurrent={this.toggleCurrent}
                    onEditAction={this.edit}
                    onDeleteAction={this.delete}
                    onSaveChanges={this.save}
                />
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
            {
                this.cancelAction();
            }
            else
            {
                if (optionType === ToDoOption.Type.Edit)
                    this.props.onEditAction(true);
                return {activeOption: optionType};
            }
        });
    },

    cancelAction: function () {
        if (this.state.activeOption === ToDoOption.Type.Edit)
            this.props.onEditAction(false);
        this.setState({activeOption: null});
    },

    confirmAction: function () {
        switch (this.state.activeOption)
        {
            case ToDoOption.Type.Today:
            case ToDoOption.Type.Later:
                this.props.onToggleCurrent();
                break;
            case ToDoOption.Type.Edit:
                this.props.onSaveChanges();
                break;
            case ToDoOption.Type.Delete:
                this.props.onDeleteAction();
                break;
            default:
                console.error("ToDoActions.confirmAction: Invalid option type: " + this.state.activeOption);
        }
        this.cancelAction();
    },

    render: function () {
        // Show all options if no option has been chosen.
        // If one has been selected, show only that option with its prompt.
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
            var actionPrompt;
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
                    console.error("ToDoAction.render: Active option has invalid type: " + this.state.activeOption);
            }

            var changePrompt = (
                <div className="to-do-change">
                    <p>{actionPrompt}</p>
                    <a className="yes" href="#" onClick={this.confirmAction}>
                        {this.state.activeOption === ToDoOption.Type.Edit ? "Save" : "Yes"}
                    </a>
                    <a className="no" href="#" onClick={this.cancelAction}>
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
    activate: function () {
        this.props.onActivate(this.props.type);
    },

    render: function () {
        var typeClassName;
        switch (this.props.type)
        {
            case ToDoOption.Type.Today:
                typeClassName = "to-do-today";
                break;
            case ToDoOption.Type.Later:
                typeClassName = "to-do-later";
                break;
            case ToDoOption.Type.Edit:
                typeClassName = "to-do-edit";
                break;
            case ToDoOption.Type.Delete:
                typeClassName = "to-do-delete";
                break;
            default:
                console.error("ToDoOption.typeClassName: Got invalid type: " + this.props.type);
        }

        return (
            <a className={"to-do-option " + typeClassName} href="#" onClick={this.activate}></a>
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
    <ToDoList />,
    document.getElementById("to-do-list-section")
);

React.render(
    <ToDoForm />,
    document.getElementById("new-to-do-form-section")
);
