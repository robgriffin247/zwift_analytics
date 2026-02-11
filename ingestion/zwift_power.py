import json
import polars as pl


def write_league_csv(league_id: int) -> None:
    input_json_path = f"data/{league_id}.json"
    rows = []

    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for event in data["data"]:
        rows.append(
            {
                "event_id": event.get("zid"),
                "event_start_epoch": event.get("tm"),
                "league_id": league_id,
            }
        )

    events = pl.DataFrame(rows)
    output_path = f"data/{league_id}.csv"
    events.write_csv(output_path)
    print(f"Wrote {output_path}")

if __name__ == "__main__":
    # copy this data to the json file then run; https://zwiftpower.com/api3.php?do=league_event_results&id=3165
    write_league_csv(3165)
