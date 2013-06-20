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

    start: function (bootstrap) {
        this.toDoList = new this.Collections.ToDoList(bootstrap.toDoList);
        var toDoListView = new this.Views.ToDoList({collection: this.toDoList, el: $('#toDoList')});
        toDoListView.render();
    }
}))({el: document.body});

App.Models.ToDoItem = Backbone.Model.extend({
    defaults: {
        title: '',
        description: '',
        done: false
    },

    check: function (checked) {
       this.set('done', checked);
    },

    rename: function (title) {
        this.set('title', title);
    }
});

App.Collections.ToDoList = Backbone.Collection.extend({
    model: App.Models.ToDoItem,

    initialize: function () {
        this.on('delete', this.remove);
        this.on('change', this.log);
    },

    log: function () {
        console.log('-----------\n');
        console.log('To Do List:\n');
        this.forEach(function (toDoItem) {
            console.log(toDoItem.get('title') +
                ': ' + (toDoItem.get('done') ? 'Done' : 'Not Done') +
                '\n');
        });
        console.log('-----------\n');
    }
});

App.Views.ToDoItem = Backbone.View.extend({
    tagName: 'li',
    className: 'toDoItem',

    /*
    template: _.template('<label>' +
        '<input type="checkbox" ' +
        '<% if (done) print("checked ") %>/>' +
        '<%= title %></label>'),
    */

    itemTemplate: Handlebars.compile('<input type="checkbox"' +
        '{{#if done}}checked {{/if}}/>' +
        '<span class="title">{{title}}</span>' +
        '<a class="delete" href="#">Delete</a>'),

    editorTemplate: Handlebars.compile('<form class="toDoEditor"><input class="edit" type="text" value="{{title}}" /></form>'),

    events: {
        'change input[type="checkbox"]': 'checkItem',
        'click span.title': 'editItem',
        'click a.delete': 'deleteItem',
        'focusout input.edit': 'submitItem',
        'submit form': 'submitItem'
    },

    initialize: function () {
        this.model.on('delete', this.remove, this);
    },

    checkItem: function () {
        this.model.check(this.$('input[type="checkbox"]').is(':checked'));
    },

    editItem: function () {
        this.$('a.delete').hide();
        this.$('span.title').hide();
        this.$el.append(this.editorTemplate({title: this.model.get('title')}));
        this.$('input.edit').focus();
    },

    deleteItem: function () {
        this.model.trigger('delete', this.model);
    },

    submitItem: function (e) {
        e.preventDefault();
        var title = this.$('input.edit').val()
        if (title)
            this.model.rename(title);
        else
            this.deleteItem();
        this.$('input.edit').remove();
        this.$('span.title').text(this.model.get('title')).show();
        this.$('a.delete').show();
    },

    render: function () {
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
    },

    render: function () {
        this.collection.forEach(this.addItem, this);
        return this;
    }
});

App.ToDoRouter = Backbone.Router.extend({});

var bootstrap = {
    toDoList: [
        { id: 1, title: 'Task 1', done: false },
        { id: 2, title: 'Task 2', done: false },
        { id: 3, title: 'Task 3', done: true }
    ]
}

App.start(bootstrap);
