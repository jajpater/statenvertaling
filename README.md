# Statenvertaling *with Apocrypha* (OSIS)

This is my fork from https://github.com/Isidore-Guild/statenvertaling

He did an excellent job in creating a solid Statenvertaling module to which the Apocrypha can be added optionally.
He used NRSVA versification for adding the apocrypha.
He corrected the module to fit NRSVA versification.

I made a patch to the swordlibrary for [DutSVV versification](https://github.com/jajpater/sword-patches)
And I have corrected the module back to fit this new versification.

## Converting

`convert_versification.py` renumbers verses whose `[HH:VV]` marker sits at the
**start** of the verse text. That is not the whole job: where the Dutch
versification splits one English verse in two, the marker sits in the
**middle** of the verse, and the verse has to be split rather than renumbered.
`repareer_versificatie.py` does that, and also merges the one case where two
English verses are a single Dutch verse.

Run it after `convert_versification.py`:

```
python3 repareer_versificatie.py STV.osis.xml STV.osis.xml
osis2mod modules/texts/ztext/stv STV.osis.xml -v DutSVV -z z
```

It is idempotent and reports what it changed. Affected in this text: 69 verses
split (63 psalm superscriptions, plus 1Kgs 22:43, Neh 7:73, John 1:38,
Rom 7:25, 3John 1:14 and Rev 12:18 — the last two of those move the split-off
part into the next chapter), and Ps 13:6 merged.

Verified against the GBS Statenvertaling module: 2522 of 2527 psalm verses
match, the five differences being edition variants at the same verse number
(`op de Neginoth` / `op Neginoth`, `Hammaaloth` / `Hammaäloth`). Strong's
numbers (482813) and footnotes (59385) are preserved exactly; footnotes follow
their catchWord into the right half of a split verse.

## TODO
Look into the versification for the apocrypha.
Maybe extend the patch to also fit these.

