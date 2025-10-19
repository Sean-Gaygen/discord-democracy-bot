"use strict";

const submitVoteURL = submitVoteURL;


//THIS IS A W.I.P.

//Pattern: [value_key, value1 func, value2 func]
const build_funcs = {
	'dissolve': [null, null],
	'add_amend': [null, null], // TODO
	'sub_amend': [null, null],  // TODO
};

function proposeeBlock() {

	let user_options = [];
	
	for (let index in users){
		
		let user_name = users[index].fields.name;
		
		user_options.push(
			<option value={user_name}>{user_name}</option>
		);
		
	}
	
	user_options.push(<option value="Random Internet User">"Random Internet User"</option>);
	user_options.push(<option value="Anonymous">"Anonymous"</option>);
	
	return <>
		
		<label for="proposee">I, </label>
		<select name="proposee" id="proposee">
			{user_options}
		</select>
	
	</>

}

function categoryBlock() {
	
	let category_options = [];
	
	for (let index in categories){
		
		let category = categories[index];
		
		category_options.push(
			<option value={category.fields.function_key}>{category.fields.words}</option>
		);
		
	}
	
	return <>
	
		<label for="category" onChange={(e) => setKey(e.target.value)}> shall make a proposal to </label>
		<select name="category" id="category">
			{category_options}
		</select>
	
	</>


}

function valueXBlock(props) {

	let func_to_run = build_funcs[props.key][props.index];
	
	if (func_to_run == null){
	
		return
		
	} else {
		
		return <func_to_run />
		
	}

}

function postFormBlurb() {

	return <>
	
		{sent_duplicate && 
		
			<p className="postFormBlurb">
				"This provision is currently being voted on. Please propose a new amendment."
			</p>
		}
		
		{too_many_provisions &&
		
			<p className="postFormBlurb">
				"There are currently 10 active polls, Please wait until one has resolved to make a new proposal."
			</p>
		
		}
		
		{from_submit & !sent_duplicate & !too_many_provisions &&
		
			<p className="postFormBlurb">
				"Your provision has been accepted. Please allow up to 5 minutes to pass for your provision to be posted, I can't afford powerful servers yet."
			</p>
		
		}
	
	</>

}

function constitutionContent(){

	let amendments = [];

	for (let index in contitution){

		let amendment = constitution[index]

		amendments.push(
			<span className="amendmentLine">{amendment.fields.amendment_text}</span>
		)

	}

	return <div className="constitutionContent">
		{amendments}
	</div>

}

function constitutionBorder(){

	return <div className="constitutionBorder">



	</div>

}

function constitutionBlock() {

	//TODO setup using a grid pattern fixed elements of the ascii, and make extendable
	// elements that simply severely overflow their borders so it doesn't matter how much
	// they get extended. Make sure that overflow is hidden so it looks like the ascii art is
	// dynamically expanding to meet the size of the screen

	`	111 222 ... 222 333
		111 222 ... 222 333
		111 222 ... 222 333
		4   5   ...   5   6
		.   5   ...   5   .
		.   5   ...   5   .
		.   5   ...   5   .
		4   5   ...   5   6
		777 888 ... 888 999
		777 888 ... 888 999
		777 888 ... 888 999
	`

	return <div className="constitutionBlock">
		
		<div className="constitutionHeader">
			<span> .-.---------------------------------.-. </span>
			<span>((o))                                   )</span>
			<span> \U/_______          _____         ____/ </span>
		</div>

		<constitutionBorder />

		<constitutionContent />

		<constitutionBorder />

		<div className="constitutionFooter">
			<span>   ____    _______    __  ____    ___   </span>
			<span> /A\                                  \ </span>
			<span>((o))                                  )</span>
			<span> '-'----------------------------------' </span>
		</div>

	
	</div>

}

function votingForm() {
	const[key, setKey] = useState("dissolve");
	
	return <>

		<div>
			<form action={submitVoteURL} method="post" id="main_form">
				
				<formset>

					<proposeeBlock />

					<categoryBlock />

					<valueXBlock key={key} index={1}/>

					<valueXBlock key={key} index={2}/>

				</formset>

				<input type="submit" value="Put to a vote" />

			</form>

			<postFormBlurb />

			<constitutionBlock />

		</div>
		
	</>

}

const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<votingForm />);