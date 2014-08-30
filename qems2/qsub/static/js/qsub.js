function add_row_to_cat_table() {
    var current_forms = parseInt($('#id_distentry-INITIAL_FORMS')[0].value);
    var next_form = current_forms + 1;
    $('#dist-table > tbody > tr:last').
	after(sprintf(
	    '<tr><td><input id="id_distentry-%d-category" width="100" type="text" name="categories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-subcategory" type="text" name="subcategories" maxlength="100" /></td> \
<td><input id="id_distentry-%d-num_tossups" width="10" type="text" class="spinner" name="num_tossups" /></td> \
<td><input id="id_distentry-%d-num_bonuses" width="10" type="text" class="spinner" name="num_bonuses" /></td> \
<td><input id="id_distentry-%d-fin_tossups" width="10" type="text" class="spinner" name="fin_tossups" /></td> \
<td><input id="id_distentry-%d-fin_bonuses" width="10" type="text" class="spinner" name="fin_bonuses" /></td> \
<td>&nbsp;</td></tr>', next_form, next_form, next_form, next_form, next_form, next_form));
    
    $('.spinner').width(10).spinner({'min': 0})
}


$(function () {
    
    tinymce.init({
	selector: 'textarea.question_text',
	menubar: false,
	toolbar: 'undo redo | bold italic underline',
	fontsize_formats: '12px 14px 16px',
	setup: function(ed) {
	    ed.on('init', function() {
		this.getDoc().body.style.fontSize='18px';
	    });
	},
        width: 900,
        // inline: true,
        formats: {
            underline: {inline: 'u', exact: true},
            italic: {inline: 'i', exact: true},
            bold: {inline: 'b', exact: true}
        }
    });
    
    $('#id_player_to_add').autocomplete({
	source: "/find_player/?tour_id=" + $('#tour_id').val() + $(this).val(),
	select: function(event, ui) {
	    $('#id_player_to_add').val(ui.item.label);
	    $('#id_hd_player_to_add').val(ui.item.value);
	    
	    return false;
	}
    }),
    
    $('#id_teammate_to_add').autocomplete({
	source: "/find_teammate/?team_id=" + $('#team_id').val() + $(this).val(),
	select: function(event, ui) {
	    $('#id_teammate_to_add').val(ui.item.label);
	    $('#id_hd_teammate_to_add').val(ui.item.value);
	    
	    return false;
	}
    })
    
    $(document).tooltip();
    
    $('.spinner').width(25).spinner({'min': 0})
    $('#add-row').click(add_row_to_cat_table)

    $('.delete_tossup').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this tossup! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            window.location = $(this).attr('href');
        }
    });

    $('.delete_bonus').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this bonus! If you do so, you will not be able to recover it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            window.location = $(this).attr('href');
        }
    });

    $('.delete_packet').click(function(e) {
        e.preventDefault();
        var result = confirm("You are about to delete this packet! If you do so, you will not be able to recover it! 99% of the time this is a terrible idea and you should not do it! Are you ABSOLUTELY SURE you want to do that?!");
        if (result == true) {
            window.location = $(this).attr('href');
        }
    });

    $('#upload-dialog').dialog({
        autoOpen: false,
        width: 600,
        height: 400,
        buttons: {
            Cancel: function() {
                $(this).dialog('close');
            },
            Ok: function() {
                $(this).find('form').submit();
            }
        }
    })

    $('#upload-questions').click(function () {
        $('#upload-dialog').dialog('open');
    })
});

