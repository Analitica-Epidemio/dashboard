import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths } from "./types";
import { env } from "@/env";

const fetchClient = createFetchClient<paths>({
  baseUrl: env.NEXT_PUBLIC_API_HOST
});

export const $api = createClient(fetchClient);