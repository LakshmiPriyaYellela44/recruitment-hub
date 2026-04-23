/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx}",
    ],
    theme: {
        extend: {
            colors: {
                'buddy-red': '#FF4757',
                'buddy-red-dark': '#FF3838',
                'buddy-red-light': '#FF2828',
            }
        },
    },
    plugins: [],
}