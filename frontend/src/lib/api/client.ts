import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

const fetchClient = createFetchClient({
  baseUrl: "http://localhost:8000",
});

export const $api = createClient(fetchClient);