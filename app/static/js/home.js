let MAX_CUSTOM_SPECIES = 1;
let SPECIES_FORM_PREFIX = ''
const help_text = document.getElementById("help_text");

function initScript(max_custom, species_prefix){
  MAX_CUSTOM_SPECIES = max_custom;
  SPECIES_FORM_PREFIX = species_prefix;
}


const job_form = document.getElementById("theForm")
const buttonClick = () => {
  const form_div = document.getElementById("formdiv")
  const job_button = document.getElementById("job_button")

  job_button.classList.remove('opacity-100');
  job_button.classList.add('opacity-0');
  setTimeout(() => {
    job_button.classList.add('hidden');
    form_div.classList.remove('hidden');
    setTimeout(() => {
      form_div.classList.remove('opacity-0');
      // form_div.classList.add('opacity-100');

    }, 50);
  }, 250);

}


  const theFile = document.getElementById("theFile");
  const checkMail = (event) => {
    const res = String(event.target.value).toLowerCase().match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
    const continue_button = document.getElementById("continue_after_mail");
    
    if (res == null) {
      event.target.classList.remove("text-green-600");
      event.target.classList.add("text-red-500");
      event.target.valid = false;
      continue_button.classList.remove("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      continue_button.classList.add("bg-gray-600","text-white")
      theFile.disabled = true;
      continue_button.removeEventListener("click", formForward)

    } else {
      event.target.classList.remove("text-red-500");
      event.target.classList.add("text-green-600");
      event.target.valid = true;
      continue_button.classList.remove("bg-gray-600","text-white")
      continue_button.classList.add("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      theFile.disabled = false;
      continue_button.addEventListener("click", formForward)
    }

  }

  const email = document.getElementById("theMail");
  email.value = ""
  email.addEventListener('input', checkMail);

  const formForward = () => {
    if (job_form[0].value) {
      document.getElementById("mail_div").classList.add("hidden");
      document.getElementById("file_div").classList.remove("hidden");
      help_text.innerText = `The reads file should be in fasta, fastq, or a gz compressed fasta. The file should contain all the reads you would like to filter.`
    }
    if (job_form[1].value) {
      const checkFile = (file_name, extensions) => {
        const file_extension = file_name.split('.').pop()
        
        if (!extensions.includes(file_extension)) {
          return false;
        }
        return true;
      }
      if(!checkFile(job_form[1].value, job_form[1].accept)) {
        job_form[1].valid = false;
        alert("please select a valid file!")
        return;
      };
      job_form[1].valid = true;
      document.getElementById("file_div").classList.add("hidden");
      document.getElementById("database_div").classList.remove("hidden");
      help_text.innerText = `Please select the database against which reads should be filtered. Please select "custom" to provide your own selection of potential contaminating organisms.`
    }
  }



  function postForm() {
    document.getElementById("submit_button").removeEventListener("click", postForm);
    document.getElementById("formdiv").classList.add("hidden")
    document.getElementById("after_post").classList.remove("hidden")

    let formdata = new FormData(document.getElementById("theForm"));
    
    let request = new XMLHttpRequest();

    request.upload.addEventListener('progress', (event) => {

      var file1Size = document.getElementById('theFile').files[0].size;
        if (event.loaded <= file1Size) {
          var percent = Math.round(event.loaded / file1Size * 100);
        //   document.getElementById('progress-bar').style.width = percent + '%';
          document.getElementById('progress-bar').innerHTML = percent + '%';
        }
        if(event.loaded == event.total){
        //   document.getElementById('progress-bar').style.width = '100%';
          document.getElementById('progress-bar').innerHTML = '100%';
        }
    });
    

    request.open('POST', '');
    request.send(formdata);

    request.onreadystatechange = () => {
        if (request.readyState == XMLHttpRequest.DONE) {
            var OK = 200;

            if (request.status === OK) {
                window.location.href = request.responseURL;
            }
            else {
                console.log ('Error: ' + request.status); 
            }
        }
    };

}

const enableSubmit = (event) => {
  const submit_button = document.getElementById("submit_button");
  const enableSubmitButton = () => {
    submit_button.classList.remove("bg-gray-600","text-white")
    submit_button.classList.add("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
    submit_button.addEventListener("click", postForm)
  }
  if (event.target.value != "") {
    enableSubmitButton()
    return true;
  }
  let sibling = event.target.parentNode.firstChild
  while (sibling){
    if (sibling.value != ""){
      enableSubmitButton()
      return true;
    }
    sibling = sibling.nextSibling
  }
  submit_button.classList.remove("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
  submit_button.classList.add("bg-gray-600","text-white")
  submit_button.removeEventListener("click", postForm)
  return false;
}

const customDBSelector = (event) => {
  const submit_button = document.getElementById("submit_button");
  submit_button.classList.remove("hover:bg-green-600","hover:text-white", "text-black", "cursor-pointer")
  submit_button.classList.add("bg-gray-600","text-white")
  submit_button.removeEventListener("click", postForm)

  const db_options = document.getElementById("DB_options");
  db_options.replaceChildren()

  for (let i = 0; i < MAX_CUSTOM_SPECIES; i++) {
    let input = document.createElement("input");
    input.setAttribute("type", "text");
    input.setAttribute("name", SPECIES_FORM_PREFIX + i);
    input.setAttribute("maxlength", "15")
    // input.setAttribute("pattern", "[A-Za-z]{0,4}[_]{0,1}[0-9]{0,10}")
    input.setAttribute("placeholder", "NCBI TAXONOMIC ID");
    input.classList = ["w-64 text-center mx-2  my-2 px-3 py-3 rounded-md uppercase  border border-blue-700"]
    db_options.appendChild(input)
  }
  help_text.innerText = `Please enter at least one valid NCBI taxonomic ID, We will build a filter based on the taxa you have entered.`
  db_options.addEventListener("input", enableSubmit)

}


theFile.addEventListener('change', formForward);
theFile.value = null

document.getElementById("custom_button").addEventListener("click", customDBSelector)
document.getElementById("submit_button").addEventListener("click", postForm)
