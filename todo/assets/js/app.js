var App = new (Backbone.View.extend({
    Models: {},
    Views: {},
    Collections: {},

    events: {
        'click #add': 'addToDoItem'
    },

    addToDoItem: function () {
        var toDoItem = new App.Models.ToDoItem();
        this.toDoList.add(toDoItem);
    },

    start: function () {
        this.toDoList = new this.Collections.ToDoList();
        var toDoListView = new this.Views.ToDoList({collection: this.toDoList, el: $('#toDoList')});
    }
}))({el: document.body});

App.Models.ToDoItem = Backbone.Model.extend({
    defaults: {
        active: false,
        description: '',
        done: false,
        routine: false,
        title: ''
    },

    initialize: function () {
        this.on('delete', this.destroy, this);
    },

    check: function (checked) {
        this.set('done', checked);
        this.save();
    },

    rename: function (title) {
        this.set('title', title);
        this.save();
    }
});

App.Collections.ToDoList = Backbone.Collection.extend({
    model: App.Models.ToDoItem,
    url: '/todo',

    initialize: function () {
        // Iterate over each todo item that has already been rendered and attach models and views to them.
        _.each($('.toDoItem'), function (toDoItemElement) {
            var id = $(toDoItemElement).data('id');
            var titleElement = $(toDoItemElement).children('span.title')[0]
            var title = $(titleElement).text();
            var done = $(toDoItemElement).children('input').is(':checked');
            var toDoItem = new App.Models.ToDoItem({
                id: id,
                title: title,
                done: done
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
            console.log(toDoItem.get('title') + ': ' + (toDoItem.get('done') ? 'Done' : 'Not Done'));
        });
        console.log('-----------');
    }
});

App.Views.ToDoItem = Backbone.View.extend({
    tagName: 'li',
    className: 'toDoItem',
    attributes: function () {
        return {
            'data-id': this.model.id
        };
    },

    // Normal state template for todo item
    itemTemplate: Handlebars.compile('<input type="checkbox" ' +
        '{{#if done}}checked {{/if}}/>' +
        '<span class="title">{{title}}</span>' +
        '<a class="delete" href="#">Delete</a>'),

    // Editing state template for todo item
    editorTemplate: Handlebars.compile('<form class="toDoEditor"><input class="edit" type="text" value="{{title}}" /></form>'),

    events: {
        'change input[type="checkbox"]': 'checkItem',
        'click span.title': 'editItem',
        'click a.delete': 'deleteItem',
        'focusout input.edit': 'submitItem',
        'submit form': 'submitItem'
    },

    initialize: function () {
        this.model.on('destroy', this.remove, this);
        this.model.on('sync', this.render, this);
        this.model.on('error', this.showError, this);
    },

    // Mark todo item as done.
    checkItem: function () {
        this.model.check(this.$('input[type="checkbox"]').is(':checked'));
    },

    // Transform the element into an editing state.
    editItem: function () {
        this.$('a.delete').hide();
        this.$('span.title').hide();
        this.$el.append(this.editorTemplate({title: this.model.get('title')}));
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
        this.collection.on('add', this.addItem, this);
    },

    addItem: function (toDoItem) {
        var toDoItemView = new App.Views.ToDoItem({model: toDoItem});
        this.$el.append(toDoItemView.render().el);
        if (!toDoItem.get('title'))
            toDoItemView.editItem();
    }
});

App.ToDoRouter = Backbone.Router.extend({});

App.start();
