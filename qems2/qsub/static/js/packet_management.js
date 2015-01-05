$(function () {

    function addTossupsToSet(e) {
        var data = $("#tossup-dialog tbody tr td input:checked");
        var qset_id = $("#qset-id").val();
        var packet_id = $("#packet-id").val();
        var tossup_ids = [];

        $.each(data, function() {
            var tossup_id = $(this).val();
            tossup_ids.push(tossup_id);
        });

        $.post('/assign_tossups_to_packet/',
               {packet_id: packet_id, tossup_ids: tossup_ids}, function(resp, status) {
                   var resp_data = $.parseJSON(resp)
                   if (status == 'success') {
                       $("#tossup-dialog").dialog("close");
                       $("#info-dialog").attr("title", "Success!");
                       $("#info-dialog").dialog("open");
                       $("#info-dialog").append("<div class='" + resp_data.message_class + "'>" + resp_data.message + "</div>");
                   }
               });
    }

    function addBonusesToSet(e) {
        var data = $("#bonus-dialog tbody tr td input:checked");
        var qset_id = $("#qset-id").val();
        var packet_id = $("#packet-id").val();
        var bonus_ids = [];

        $.each(data, function() {
            var bonus_id = $(this).val();
            bonus_ids.push(bonus_id);
        });

        $.post('/assign_bonuses_to_packet/',
               {packet_id: packet_id, bonus_ids: bonus_ids}, function(resp, status) {
                   var resp_data = $.parseJSON(resp)
                   if (status == 'success') {
                       $("#bonus-dialog").dialog("close");
                       $("#info-dialog").attr("title", "Success!");
                       $("#info-dialog").dialog("open");
                       $("#info-dialog").append("<div class='" + resp_data.message_class + "'>" + resp_data.message + "</div>");
                   }
               });
    }

    $("#add-existing-tossups").click(function (e) {
        data = $.ajax({url: "/get_unassigned_tossups/", data: {qset_id: $("#qset-id").val()}}).done(function (data) {
            var json_data = $.parseJSON(data);
            var dialog = $("#tossup-dialog")

            if (_.isEmpty(json_data)) {
                dialog.empty();
                dialog.append("<div class='alert-box warning'>There are no unassigned tossups to add!</div>")
                dialog.dialog("option", "buttons", [ { text: "OK", click: function() { $(this).dialog("close") }}])
                dialog.dialog("open");
            }
            else {
                dialog.dialog("open");
                _.each(json_data, function (item) {
                    console.log(item['tossup_answer']);
                    dialog_tbody = $("#tossup-dialog tbody");
                    var html = "<tr><td>" + item.tossup_answer.substr(0,40) + "...</td>" +
                        "<td>" + item.category_name + "</td>" +
                        "<td><input type='checkbox' value='" + item.id + "'/></td></tr>";
                    dialog_tbody.append(html);
                })
                $("#tossup-dialog").dialog("option","height",$("#tossup-dialog table").height()+200);
            }
        })
    })

    $("#add-existing-bonuses").click(function (e) {
        data = $.ajax({url: "/get_unassigned_bonuses/", data: {qset_id: $("#qset-id").val()}}).done(function (data) {
            var json_data = $.parseJSON(data);
            var dialog = $("#bonus-dialog")

            if (_.isEmpty(json_data)) {
                dialog.empty();
                dialog.append("<div class='alert-box warning'>There are no unassigned bonuses to add!</div>")
                dialog.dialog("option", "buttons", [ { text: "OK", click: function() { $(this).dialog("close") }}])
                dialog.dialog("open");
            }
            else {
                dialog.dialog("open");
                _.each(json_data, function (item) {
                    dialog_tbody = $("#bonus-dialog tbody");
                    var html = "<tr><td>" + item.leadin.substr(0,40) + "...</td>" +
                        "<td>" + item.category_name + "</td>" +
                        "<td><input type='checkbox' value='" + item.id + "'/></td></tr>";
                    dialog_tbody.append(html);
                })
                $("#bonus-dialog").dialog("option","height",$("#bonus-dialog table").height()+200);
            }
        })
    })

    $("#tossup-dialog").dialog({
        autoOpen: false,
        closeOnEscape: true,
        width: 640,
        modal: true,
        buttons: {
            "Add Selected Tossups": addTossupsToSet,
            Cancel: function() {
                $(this).dialog("close");
            }
        },
        close: function() {
            $("#tossup-dialog tbody").empty();
        }
    })

    $("#bonus-dialog").dialog({
        autoOpen: false,
        closeOnEscape: true,
        width: 640,
        modal: true,
        buttons: {
            "Add Selected Bonuses": addBonusesToSet,
            Cancel: function() {
                $(this).dialog("close");
            }
        },
        close: function() {
            $("#bonus-dialog tbody").empty();
        }
    })

    var sortableOptionsTossups = { axis: "y", containment: "#tossup-table" };
    var sortableOptionsBonuses = { axis: "y", containment: "#bonus-table" };

    var tossupTable = $("#tossup-table tbody");
    tossupTable.sortable(sortableOptionsTossups);
    tossupTable.on("sortstart", function (event, ui) {
        ui.item.data("initialIndex", ui.item.index());
    });

    tossupTable.on("sortupdate", function (event, ui) {
        var order_data = []
        var packet_id = $("#packet-id").val();
        $("#tossup-table tr").each(function(index, row) {
            if (index > 0) {
                $(this).children('td').first().text(index);
                $(this).attr('value', index);
                order_data.push({id: $(this).attr('tossup-id'),
                                 order: index})
            }
        });
        $.post("/change_question_order/", {packet_id: $('#packet-id').attr('value'),
                                      order_data: order_data,
                                      num_questions: order_data.length,
                                      question_type: 'tossup'},
               function(response, status) {
                   if (status == 'success') {
                       var resp_data = $.parseJSON(response);
                       var message = resp_data.message
                       var message_class = resp_data.message_class
                       if (message != '') {
                           var dialog = $('#info-dialog').dialog({
                               modal: true,
                               buttons: {
                                   Ok: function() {
                                       $(this).dialog('close');
                                   }
                               }
                           });
                           dialog.append('<div class="' + message_class + '">' + message + '</div>');
                           dialog.dialog('open');
                       }
                   }
               });
    });

    var bonusTable = $("#bonus-table tbody");
    bonusTable.sortable(sortableOptionsBonuses);
    bonusTable.on("sortstart", function (event, ui) {
        ui.item.data("initialIndex", ui.item.index());
    });
    bonusTable.on("sortupdate", function (event, ui) {
        var order_data = []
        var packet_id = $("#packet-id").val();
        $("#bonus-table tr").each(function(index, row) {
            if (index > 0) {
                $(this).children('td').first().text(index);
                $(this).attr('value', index);
                order_data.push({id: $(this).attr('bonus-id'),
                                 order: index})
            }
        });
        $.post("/change_question_order/", {packet_id: $('#packet-id').attr('value'),
                                      order_data: order_data,
                                      num_questions: order_data.length,
                                      question_type: 'bonus'},
               function(response, status) {
                   if (status == 'success') {
                       var resp_data = $.parseJSON(response);
                       var message = resp_data.message
                       var message_class = resp_data.message_class
                       if (message != '') {
                           var dialog = $('#info-dialog').dialog({
                               modal: true,
                               buttons: {
                                   Ok: function() {
                                       $(this).dialog('close');
                                   }
                               }
                           });
                           dialog.append('<div class="' + message_class + '">' + message + '</div>');
                           dialog.dialog('open');
                       }
                   }
               });
    });


    $("#info-dialog").dialog({
        autoOpen: false,
        height: 200,
        width: 600,
        modal: true,
        buttons: {
            Ok: function() {
                $(this).dialog("close");
            }
        }
    })

    /*$("#tossup-table").tableDnD({
        onDrop: function(table, row) {
            var rows = table.tBodies[0].rows;
            var order_data = []
            var packet_id = $("#packet-id").val();
            $("#tossup-table tr").each(function(index, row) {
                if (index > 0) {
                    $(this).children('td').first().text(index);
                    $(this).attr('value', index);
                    order_data.push({id: $(this).attr('tossup-id'),
                                     order: index})
                }
            });
            
            console.log(order_data)
            $.post('/set_tossup_order/', {packet_id: packet_id, order_data: order_data}, function(response) {
                console.log(response);
            });
        }
    });*/
})
