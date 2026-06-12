import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/router";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function AddElder() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    phone_number: "",
    language: "hindi",
    call_time: "09:00",
  });
  const [contacts, setContacts] = useState([
    { name: "", phone: "", priority: 1 }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!form.name || !form.phone_number) {
      alert("Please fill in name and phone number!");
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/elders`, {
        ...form,
        family_contacts: contacts.filter(c => c.name && c.phone)
      });
      alert(`${form.name} added successfully!`);
      router.push("/");
    } catch (e) {
      alert("Failed to add elder: " + e.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const addContact = () => {
    setContacts([...contacts, {
      name: "", phone: "", priority: contacts.length + 1
    }]);
  };

  const updateContact = (index, field, value) => {
    const updated = [...contacts];
    updated[index][field] = value;
    setContacts(updated);
  };

  return (
    <div className="min-h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-2xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <button className="text-gray-500 hover:text-gray-700">
                ← Back
              </button>
            </Link>
            <h1 className="text-xl font-bold text-gray-800">
              Add New Elder
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border space-y-5">

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              placeholder="e.g. Dadi Ji"
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Phone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number *
            </label>
            <input
              type="text"
              placeholder="+919876543210"
              value={form.phone_number}
              onChange={e => setForm({...form, phone_number: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Language
            </label>
            <select
              value={form.language}
              onChange={e => setForm({...form, language: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="hindi">Hindi</option>
              <option value="english">English</option>
              <option value="punjabi">Punjabi</option>
            </select>
          </div>

          {/* Call Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Daily Call Time
            </label>
            <input
              type="time"
              value={form.call_time}
              onChange={e => setForm({...form, call_time: e.target.value})}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Family Contacts */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Family Contacts
              </label>
              <button
                onClick={addContact}
                className="text-blue-600 text-sm hover:underline">
                + Add Contact
              </button>
            </div>
            <div className="space-y-3">
              {contacts.map((contact, i) => (
                <div key={i} className="grid grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="Name"
                    value={contact.name}
                    onChange={e => updateContact(i, "name", e.target.value)}
                    className="border rounded-lg px-3 py-2 text-sm"
                  />
                  <input
                    type="text"
                    placeholder="+91XXXXXXXXXX"
                    value={contact.phone}
                    onChange={e => updateContact(i, "phone", e.target.value)}
                    className="border rounded-lg px-3 py-2 text-sm"
                  />
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Priority</span>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={contact.priority}
                      onChange={e => updateContact(i, "priority", parseInt(e.target.value))}
                      className="border rounded-lg px-3 py-2 text-sm w-16"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {loading ? "Adding..." : "Add Elder"}
          </button>
        </div>
      </div>
    </div>
  );
}