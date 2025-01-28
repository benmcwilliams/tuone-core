```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Albert-Ludwigs-University-of-Freiburg" or company = "Albert Ludwigs University of Freiburg")
sort location, dt_announce desc
```
