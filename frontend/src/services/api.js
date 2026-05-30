import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://equityguard-f02r.onrender.com";

export const checkBias = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/check-bias`, data);
    return response.data;
  } catch (error) {
    console.error("Error checking bias:", error);
    throw error;
  }
};

export const auditOrganization = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/audit`, data);
    return response.data;
  } catch (error) {
    console.error("Error auditing organization:", error);
    throw error;
  }
};
