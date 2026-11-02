{
  "rules": {
    ".read": "auth !== null",
    ".write": false,

    "users": {
      "$uid": {
        ".write": "auth.uid === $uid"
      }
    },

    "questions": {
      "$qid": {
        ".write": "auth !== null && 
          (newData.child('sender').val() === auth.uid) && 
          (!data.exists() || data.child('sender').val() === auth.uid)"
      }
    },

    "answers": {
      "$qid": {
        "$rid": {
          ".write": "auth !== null && 
            (newData.child('sender').val() === auth.uid) && 
            (!data.exists() || data.child('sender').val() === auth.uid)",
        }
      }
    }
  }
}