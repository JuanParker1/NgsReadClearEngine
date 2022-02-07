const buttonClick = () => {
    const job_form = document.getElementById("theForm")
    const job_button = document.getElementById("job_button")

    job_button.classList.remove('opacity-100');
    job_button.classList.add('opacity-0');
    job_button.classList.add('hidden');

    job_form.classList.remove("invisible");
    job_form.classList.remove("absolute", "bottom-0", "left-0");
    job_form.classList.add('opacity-100');
  }

  const theFile = document.getElementById("theFile");
  const checkMail = (event) => {
    const res = String(event.target.value).toLowerCase().match(
      /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
    const button_label = document.getElementById("button_label");

    if (res == null) {
      event.target.classList.remove("text-green-600");
      event.target.classList.add("text-red-500");
      event.target.valid = false;
      button_label.classList.remove("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      button_label.classList.add("bg-gray-600","text-white")
      theFile.disabled = true;

    } else {
      event.target.classList.remove("text-red-500");
      event.target.classList.add("text-green-600");
      event.target.valid = true;
      button_label.classList.remove("bg-gray-600","text-white")
      button_label.classList.add("hover:bg-green-600","hover:text-white", "text-green-600", "cursor-pointer")
      theFile.disabled = false;
    }

  }

  const email = document.getElementById("theMail");
  email.value = ""
  email.addEventListener('input', checkMail);

  
  const validateInput = (event) => {
    
    if (event.target.form[0].valid) {
        const job_form = document.getElementById("theForm")
        const after_post = document.getElementById("after_post")

        job_form.classList = ['hidden'];
        after_post.classList.remove("hidden")
        postFile()

    }
  }






  function postFile() {
    let formdata = new FormData();

    formdata.append('file', document.getElementById("theFile").files[0]);
    formdata.append('email', document.getElementById("theMail").value);

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


theFile.addEventListener('change', validateInput);


// // Because we want to access DOM nodes,
// // we initialize our script at page load.
// window.addEventListener( 'load', function () {

//   // These variables are used to store the form data
//   const mail = document.getElementById( "theMail" );
//   const file = {
//         dom    : document.getElementById( "theFile" ),
//         binary : null
//       };

//   // Use the FileReader API to access file content
//   const reader = new FileReader();

//   // Because FileReader is asynchronous, store its
//   // result when it finishes to read the file
//   reader.addEventListener( "load", function () {
//     file.binary = reader.result;
//   } );

//   // At page load, if a file is already selected, read it.
//   console.log(file)
//   if( file.dom.files[0] ) {
//     reader.readAsBinaryString( file.dom.files[0] );
//   }
//   // If not, read the file once the user selects it.
//   file.dom.addEventListener( "change", function () {
//     if( reader.readyState === FileReader.LOADING ) {
//       reader.abort();
//     }

//     reader.readAsBinaryString( file.dom.files[0] );
//     sendData();
//   } );

//   // sendData is our main function
//   function sendData() {
//     // If there is a selected file, wait it is read
//     // If there is not, delay the execution of the function
//     if( !file.binary && file.dom.files.length > 0 ) {
//       setTimeout( sendData, 10 );
//       return;
//     }

//     // To construct our multipart form data request,
//     // We need an XMLHttpRequest instance
//     const XHR = new XMLHttpRequest();

//     // We need a separator to define each part of the request
//     const boundary = "blob";

//     // Store our body request in a string.
//     let data = "";

//     // So, if the user has selected a file
//     if ( file.dom.files[0] ) {
//       // Start a new part in our body's request
//       data += "--" + boundary + "\r\n";

//       // Describe it as form data
//       data += 'content-disposition: form-data; '
//       // Define the name of the form data
//             + 'name="'         + file.dom.name          + '"; '
//       // Provide the real name of the file
//             + 'filename="'     + file.dom.files[0].name + '"\r\n';
//       // And the MIME type of the file
//       data += 'Content-Type: ' + file.dom.files[0].type + '\r\n';

//       // There's a blank line between the metadata and the data
//       data += '\r\n';

//       // Append the binary data to our body's request
//       data += file.binary + '\r\n';
//     }

//     // Text data is simpler
//     // Start a new part in our body's request
//     data += "--" + boundary + "\r\n";

//     // Say it's form data, and name it
//     data += 'content-disposition: form-data; name="' + mail.name + '"\r\n';
//     // There's a blank line between the metadata and the data
//     data += '\r\n';

//     // Append the text data to our body's request
//     data += mail.value + "\r\n";

//     // Once we are done, "close" the body's request
//     data += "--" + boundary + "--";

//     // Define what happens on successful data submission
//     XHR.addEventListener( 'load', function( event ) {
//       alert( 'Yeah! Data sent and response loaded.' );
//     } );

//     // Define what happens in case of error
//     XHR.addEventListener( 'error', function( event ) {
//       alert( 'Oops! Something went wrong.' );
//     } );

//     // Set up our request
//     XHR.open( 'POST', 'http://genomefltr.tau.ac.il/upload' );

//     // Add the required HTTP header to handle a multipart form data POST request
//     XHR.setRequestHeader( 'Content-Type','multipart/form-data; boundary=' + boundary );

//     // And finally, send our data.
//     XHR.send( data );
//   }

//   // Access our form...
//   const form = document.getElementById( "theForm" );

//   // ...to take over the submit event
//   form.addEventListener( 'submit', function ( event ) {
//     event.preventDefault();
//     sendData();
//   } );
// } );
