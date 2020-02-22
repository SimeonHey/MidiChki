import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

@Injectable({
  providedIn: "root"
})
export class DataFetcherService {
  rootUrl = "https://mighty-island-21925.herokuapp.com";
  constructor(private http: HttpClient) {}

  public getAll() {
    return this.http.get(`${this.rootUrl}/getAll`);
  }
}
