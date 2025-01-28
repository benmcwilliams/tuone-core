```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Korea-Hydro-&-Nuclear-Power" or company = "Korea Hydro & Nuclear Power")
sort location, dt_announce desc
```
