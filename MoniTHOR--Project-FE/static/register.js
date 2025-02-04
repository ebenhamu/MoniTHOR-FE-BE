    document.addEventListener('DOMContentLoaded', function() {
    const regform = document.getElementById('register-form');
    console.log('regform:', regform);  // Debugging log

    if (regform) {
        try {
        regform.addEventListener('submit', function(event) {
            console.log('register-form is submitted!');
            event.preventDefault();

            let UserName = document.getElementById('username').value;
            let Password1 = document.getElementById('password1').value;
            let Password2 = document.getElementById('password2').value;
            console.log(`username=${UserName}&password1=${Password1}&password2=${Password2} Register!`);
            Register(UserName, Password1, Password2);
        }); }
        catch (error) {
            console.error('Regform error:', error);
        }
    } else {
        console.warn('register-form not found');
    }

    async function Register(UserName, Password1, Password2) {
        console.log("in function");

        try {
            let response = await fetch('/register_user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: UserName, password1: Password1, password2: Password2 })
            });
            
            let data = await response.json();
            
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
});





