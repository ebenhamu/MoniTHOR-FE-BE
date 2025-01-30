const regform = document.getElementById('register-form');

regform.addEventListener('submit', function(event) {
    console.log('register-form is submitted!');
    event.preventDefault();

    let UserName = document.getElementById('username').value;
    let Password1 = document.getElementById('password1').value;
    let Password2 = document.getElementById('password2').value;
    console.log(`username=${UserName}&password1=${Password1}&password2=${Password2} Register!`);
    Register(UserName, Password1, Password2);
});




async function Register(UserName, Password1, Password2) {
    console.log("in function");

    try {
        let response = await fetch('http://34.217.100.13:5000/BEregister', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: UserName, password1: Password1, password2: Password2 })
        });

        console.log("after fetch");

        let data = await response.json();
        console.log(data);

        if (data.message && data.message.includes("Registered successfully")) {
            alert('Registered successfully');
            window.location.href = '/login';
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// async function Register(UserName, Password1, Password2) {
//     console.log("in function")
//     let response = await fetch('http://127.0.0.1:5000/BEregister', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ username: UserName, password1: Password1, password2: Password2 })
//     });
//     console.log("after fetch")

//     let data = await response.json();
//     console.log(data);

//     if (data.message && data.message.includes("Registered successfully")) {
//         // Redirect to the login page after successful registration
//         alert('Registered successfully');
//         window.location.href = '/login';
//     } else {
//         // If registration failed, show the server's error message
//         alert(data.error || 'Registration failed');
//     }
// }




// const regform = document.getElementById('register-form');

// regform.addEventListener('submit', function(event) {
//     console.log('register-form is submitted!');
//     event.preventDefault();

//     let UserName = document.getElementById('username').value;
//     let Password1 = document.getElementById('password1').value;
//     let Password2 = document.getElementById('password2').value;
//     console.log(`username=${UserName}&password1=${Password1}&password2=${Password2} Register!`);
//     Register(UserName, Password1, Password2)
// })

// async function Register(UserName, Password1, Password2) {
//     let response = await fetch(`/register?username=${UserName}&password1=${Password1}&password2=${Password2}`);
//     let data = await response.text();
//     console.log(data);

//     if (data.includes("Registered successfully")) {
//         // Redirect to the login page after successful registration
//         alert('Registered successfully')
//         window.location.href = '/login';
//     } else {
//         // If registration failed, show the server's error message
//         alert(data);
//     }
// }