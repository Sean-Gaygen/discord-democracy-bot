"use strict";

class Voting{

	static DEBUG;
	static main_form;
	static proposee_div;
	static category_div;
	static category_select;
	static value1_div;
	static value2_div;
	static post_form_blurb;
	static users;
	static roles;
	static constitution;
	static categories;
	static from_submit;
	static sent_duplicate;
	static too_many_provisions;

	static init(){

		Voting.DEBUG = 1;
		Voting.main_form = document.getElementById("main_formset");
		Voting.proposee_div = document.getElementById("proposee_block");
		Voting.category_div = document.getElementById("category_block");
		Voting.value1_div = document.getElementById("value1_block");
		Voting.value2_div = document.getElementById("value2_block");
		Voting.post_form_blurb = document.getElementById("post_form_blurb");

		Voting.category_div.addEventListener('change', Voting.category_change);

		Voting.users = users;
		Voting.roles = roles;
		Voting.constitution = constitution;
		Voting.categories = categories;
		Voting.from_submit = from_submit;
		Voting.sent_duplicate = sent_duplicate;
		Voting.too_many_provisions = too_many_provisions;

		if (Voting.DEBUG){
			console.log('init');
			console.log(Voting.from_submit, Voting.sent_duplicate, Voting.too_many_provisions)
		}

		Voting.generate_proposee_block();
		Voting.generate_categories_block();
		Voting.generate_post_form_blurb();

	}

	static category_change(){

		if (Voting.DEBUG){
			console.log('select change', Voting.category_select, Voting.category_select.value);
		}

		Voting.clean_optionals();

		switch (Voting.category_select.value){

			case "add_amend":

				Voting.generate_add_amend();
				break;

			case "sub_amend":

				Voting.generate_sub_amend();
				break;

		}

	}

	static generate_proposee_block(){

		Voting.proposee_div.appendChild(Voting.generate_label("proposee", "I, "));

		let select_elem = Voting.generate_select('proposee');
		select_elem.setAttribute('name', 'proposee');
		select_elem.setAttribute('id', 'proposee');

		for (let index in Voting.users){

			let user = Voting.users[index];

			let option = document.createElement("option");
			option.setAttribute("value", user.fields.name);
			option.innerText = `${user.fields.name}`;

			select_elem.appendChild(option)

		}

		let rando_option = document.createElement("option");
		rando_option.setAttribute("value", "Random internet user");
		rando_option.innerText = "Random internet user";

		let anon_option = document.createElement("option");
		anon_option.setAttribute("value", "Anonymous");
		anon_option.innerText = "Anonymous";

		select_elem.appendChild(rando_option);
		select_elem.appendChild(anon_option);

		Voting.proposee_div.appendChild(select_elem)

	}

	static generate_categories_block(){

		Voting.category_div.appendChild(Voting.generate_label("category", " shall make a proposal to "));

		let select_elem = Voting.generate_select('category');
		select_elem.setAttribute('name', 'category');
		select_elem.setAttribute('id', 'category');

		for (let index in Voting.categories){

			let category = Voting.categories[index];

			let option = document.createElement("option");
			option.setAttribute("value", category.fields.function_key);
			option.innerText = `${category.fields.words}`;

			select_elem.appendChild(option)

		}

		Voting.category_div.appendChild(select_elem);

		Voting.category_select = document.getElementById('category');

	}

	static generate_post_form_blurb(){

		if (Voting.DEBUG){
			console.log(Voting.sent_duplicate, Voting.too_many_provisions, Voting.from_submit);
		}

		if (Voting.sent_duplicate){

			let blurb = document.createElement("p");
			blurb.innerText = "This provision is currently being voted on. Please propose a new amendment.";

			Voting.post_form_blurb.appendChild(blurb)

		}

		if (Voting.too_many_provisions){

			let blurb = document.createElement("p");
			blurb.innerText = "There are currently 10 active polls, Please wait until one has resolved to make a new proposal.";

			Voting.post_form_blurb.appendChild(blurb)

		}

		if (Voting.from_submit && !Voting.sent_duplicate && !Voting.too_many_provisions){

			let blurb = document.createElement("p");
			blurb.innerText = "Your provision has been accepted. Please allow up to 5 minutes to pass for your provision to be posted, I can't afford powerful servers yet.";

			Voting.post_form_blurb.appendChild(blurb)

		}

	}

	static generate_add_amend(){

		Voting.value1_div.setAttribute("display", "block");

		Voting.value1_div.appendChild(Voting.generate_label("gug", "The following amendment shall be added to our constitution verbatim (numbering is automatic. DO NOT include a number at the beginning):"));
		Voting.value1_div.appendChild(document.createElement("br"));
		let text_box = document.createElement("textarea");
		text_box.setAttribute("name", "value1");
		text_box.setAttribute("maxlength", 1000); // TODO: remove magic number

		Voting.value1_div.appendChild(text_box);

	}

	static generate_sub_amend(){

		Voting.value1_div.setAttribute("display", "block");

		let name = "sub_amend";

		Voting.value1_div.appendChild(Voting.generate_label(name, "The following amendment shall be struck from our constitution:"));
		Voting.value1_div.appendChild(document.createElement("br"));
		let select_elem = Voting.generate_select(name);
		select_elem.setAttribute("name", "value1");

		for (let index in Voting.constitution){

			let amendment = Voting.constitution[index];

			if (Voting.DEBUG){
				console.log(amendment.fields);
			}

			if (!amendment.fields.deprecated) {

				let option = document.createElement("option");
				option.setAttribute("value", amendment.pk.toString());
				option.innerText = `${amendment.pk}. - ${amendment.fields.amendment_text}`;

				select_elem.appendChild(option);

			}

		}

		Voting.value1_div.appendChild(select_elem);

	}

	static clean_optionals(){

		Voting.value1_div.replaceChildren();
		Voting.value1_div.setAttribute("display", "none");
		Voting.value2_div.replaceChildren();
		Voting.value2_div.setAttribute("display", "none");
		

	}

	static generate_label(for_text, words){

		let ret_elem = document.createElement("label");
		ret_elem.setAttribute("for", for_text);
		ret_elem.textContent = words;

		return ret_elem;
	}

	static generate_select(name){

		let ret_elem = document.createElement("select");
		ret_elem.setAttribute("name", name);
		ret_elem.setAttribute("id", name);

		return ret_elem;
	}

}

document.addEventListener('DOMContentLoaded', Voting.init);