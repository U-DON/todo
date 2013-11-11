var _sync = Backbone.sync;
Backbone.sync = function (method, model, options) {
    options.beforeSend = function (xhr) {
        var token = $('meta[name="csrf-token"]').attr('content');
        xhr.setRequestHeader('X-CSRFToken', token);
    };
    return _sync(method, model, options);
};

var App = new (Backbone.View.extend({
    Models: {},
    Views: {},
    Collections: {},

    events: {
        'click a[href="add"]': 'showToDoForm',
        'click a[href="now"]': 'showNowList',
        'click a[href="later"]': 'showLaterList',
        'click a[href="done"]': 'showDoneList'
    },

    start: function () {
        this.toDoList = new this.Collections.ToDoList();
        var toDoListView = new this.Views.ToDoList({ collection: this.toDoList, el: $('#to-do-list') });
    },

    setCurrentList: function (listName) {
        currentList = this.toDoList;
        currentList.fetch({ url: '/api/todo/' + listName,
            success: function (collection, response, options) {
                currentList.set(response.objects);
            }
        });
    },

    showNowList: function (e) {
        e.preventDefault();
        this.setCurrentList('now');
    },

    showLaterList: function (e) {
        e.preventDefault();
        this.setCurrentList('later');
    },

    showDoneList: function (e) {
        e.preventDefault();
        this.setCurrentList('done');
    },

    showToDoForm: function (e) {
        e.preventDefault();
        var toDoItem = new this.Models.ToDoItem();
        var toDoForm = new this.Views.ToDoForm({ model: toDoItem });
        this.$el.append(toDoForm.render().el);
    }
}))({el: document.body});

App.Models.ToDoItem = Backbone.Model.extend({
    urlRoot: '/api/todo',

    defaults: {
        current: false,
        description: '',
        done: false,
        routine: false,
        title: ''
    },

    initialize: function () {
        this.on('delete', this.remove, this);
    },

    validate: function (attrs, options) {
        var errors = [];
        if (!attrs.title) {
            errors.push({ name: 'title', message: 'Title is required.' });
        }
        if (attrs.current == undefined) {
            errors.push({ name: 'current', message: 'Need to know when to do.' });
        }
        if (attrs.routine == undefined) {
            errors.push({ name: 'routine', message: 'Need to know if it repeats.' });
        }
        return errors.length > 0 ? errors : false;
    },

    check: function (checked) {
        this.save({ done: checked }, {
            success: _.bind(function (model, xhr, options) {
                // Server returns done time in milliseconds once task is successfully marked done, so that needs to be updated.
                // Just to keep all attributes up-to-date, set everything according to the response.
                this.set(model.attributes);
            }, this),
            error: _.bind(function (model, xhr, options) {
                this.set(model.previousAttributes());
            }, this),
            wait: true
        });
    },

    readableDoneTime: function () {
        // Done time is in milliseconds from the epoch, so convert to be readable.
        return (new Date(this.get('doneTime'))).toString();
    },

    remove: function () {
        this.destroy({ wait: true });
    },

    rename: function (title) {
        this.save({ title: title }, {
            error: _.bind(function (model, xhr, options) {
                this.set(model.previousAttributes());
            }, this),
            wait: true
        });
    }
});

App.Collections.ToDoList = Backbone.Collection.extend({
    model: App.Models.ToDoItem,
    url: '/api/todo',

    initialize: function () {
        // Iterate over each todo item that has already been rendered and attach models and views to them.
        _.each($('.to-do-item'), function (toDoItemElement) {
            var id = $(toDoItemElement).data('id');
            var titleElement = $(toDoItemElement).children('span.title')[0];
            var title = $(titleElement).text();
            var done = $(toDoItemElement).children('input').is(':checked');
            var doneTime = (new Date($(toDoItemElement).data('done-time')));
            var toDoItem = new App.Models.ToDoItem({
                id: id,
                title: title,
                done: done,
                doneTime: doneTime
            });
            this.add(toDoItem);
            var toDoItemView = new App.Views.ToDoItem({
                model: toDoItem,
                el: toDoItemElement
            });
        }, this);
        this.on('destroy', this.remove, this);
        this.on('destroy', this.log, this);
        this.on('sync', this.log, this);
    },

    // Logging to inspect models in the collection after each successful change with the server.
    log: function () {
        console.log('-----------');
        console.log('To Do List:');
        this.forEach(function (toDoItem) {
            console.log(toDoItem.get('title') + ': ' + (toDoItem.get('done') ? 'Done (' + toDoItem.readableDoneTime() + ')' : 'Not Done'));
        });
        console.log('-----------');
    }
});

App.Views.ToDoItem = Backbone.View.extend({
    tagName: 'li',
    className: 'to-do-item',
    attributes: function () {
        return {
            'data-id': this.model.id,
            'data-done-time': this.model.get('doneTime')
        };
    },

    // Normal state template for todo item
    itemTemplate: Handlebars.compile('<input type="checkbox" ' +
        '{{#if done}}checked {{/if}}/>' +
        '<span class="title">{{title}}</span>' +
        '<a class="delete" href="#">Delete</a>'
    ),

    // Editing state template for todo item
    editorTemplate: Handlebars.compile('<form class="to-do-editor">' +
        '<input class="edit" type="text" value="{{title}}" />' +
        '</form>'
    ),

    events: {
        'change input[type="checkbox"]': 'checkItem',
        'click span.title': 'editItem',
        'click a.delete': 'deleteItem',
        'focusout input.edit': 'submitItem',
        'submit form.to-do-editor': 'submitItem'
    },

    initialize: function () {
        this.listenTo(this.model, 'remove', this.remove);
        this.listenTo(this.model, 'destroy', this.remove);
        this.listenTo(this.model, 'sync', this.render);
        this.listenTo(this.model, 'error', this.showError);
    },

    // Mark todo item as done.
    checkItem: function () {
        this.model.check(this.$('input[type="checkbox"]').is(':checked'));
    },

    // Transform the element into an editing state.
    editItem: function () {
        this.$('a.delete').hide();
        this.$('span.title').hide();
        this.$('span.done-time').hide();
        this.$el.append(this.editorTemplate({ title: this.model.get('title') }));
        this.$('input.edit').focus();
    },

    // Confirm user action to delete todo item.
    deleteItem: function () {
        if (confirm('Are you sure you want to delete?')) this.model.trigger('delete');
    },

    // Display error when todo item is not successfully synced with server.
    showError: function (model, xhr) {
        console.log('There was a problem saving model:\n' + JSON.stringify(model.toJSON()) +
                    '\nxhr: ' + xhr.status + ' ' + xhr.responseText);
        this.render();
    },

    // If user presses Enter or focuses out of the input, submit the changes to todo item.
    submitItem: function (e) {
        e.preventDefault();
        var title = this.$('input.edit').val()
        if (title)
            this.model.rename(title);
        else
            // If missing a title, remove todo item if it hasn't been synced with server.
            // Confirm user action to delete for an already existing todo item.
            if (this.model.isNew())
                this.model.trigger('delete');
            else
                this.deleteItem();
    },

    render: function () {
        this.$el.attr(this.attributes());
        this.$el.html(this.itemTemplate(this.model.toJSON()));
        return this;
    }
});

App.Views.ToDoList = Backbone.View.extend({
    tagName: 'ul',

    initialize: function () {
        this.listenTo(this.collection, 'add', this.addItem);
    },

    addItem: function (toDoItem) {
        var toDoItemView = new App.Views.ToDoItem({ model: toDoItem });
        this.$el.append(toDoItemView.render().el);
        if (!toDoItem.get('title'))
            toDoItemView.editItem();
    }
});

App.Views.ToDoForm = Backbone.View.extend({
    events: {
        'click a.close': 'close',
        'submit form.to-do-form': 'submitItem'
    },

    initialize: function () {
        this.listenTo(this.model, 'invalid', this.showErrors);
    },

    close: function () {
        this.$el.remove();
    },

    serialize: function () {
        var title = $.trim(this.$('input[name="title"]').val());
        var routine = this.$('select[name="routine"]').val() == 1;
        var current = this.$('select[name="current"]').val() == 1;
        return {
            title: title,
            routine: routine,
            current: current
        };
    },

    showErrors: function (model, errors, options) {
        var that = this;
        $.each(errors, function () {
            console.log(this.name);
            console.log(this.message);
            that.$('div.form-errors').html('');
            that.$('div.form-errors').append('<p>' + this.message + '</p>');
        });
    },

    submitItem: function (e) {
        e.preventDefault();
        this.model.save(this.serialize(), {
            success: _.bind(function (model, response, options) {
                this.close();
                App.toDoList.add(model);
            }, this),
            error: function (model, xhr, options) {
            },
            wait: true
        });
    },

    render: function () {
        this.$el.html('<form class="to-do-form">\n' +
            '<label>Title</label> <input type="text" name="title" value="" />\n' +
            '<select name="routine">\n' +
            '<option value="0">once</option>\n' +
            '<option value="1">repeatedly</option>\n' +
            '</select>\n' +
            '<select name="current">\n' +
            '<option value="1">now</option>\n' +
            '<option value="0">later</option>\n' +
            '</select>\n' +
            '</form><a class="close" href="#">x</a>\n' + 
            '<div class="form-errors"></div>'
        );
        return this;
    }
});

App.ToDoRouter = Backbone.Router.extend({});

App.start();
