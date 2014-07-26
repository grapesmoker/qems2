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
	
	tinyMCE.init({
		mode: "specific_textareas",
		editor_selector: 'question_text',
		theme: "simple",
		content_css : "/static/css/custom_content.css",
		theme_advanced_font_sizes: "10px,12px,13px,14px,16px,18px,20px",
		font_size_style_values : "10px,12px,13px,14px,16px,18px,20px",
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
	
	$('.spinner').width(10).spinner({'min': 0})
	$('#add-row').click(add_row_to_cat_table)
		
})

