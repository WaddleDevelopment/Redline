﻿using System;
using UnityEngine;
using UnityEngine.UI;

public class DeathScreenController : MonoBehaviour
{

	private int _hpRating;
	private int _flameRating;
	private int _timeRating;
	private int _overallRating;

	[SerializeField] private GameMaster _gameMaster;
	[SerializeField] private float _starWidth = 100;
	[SerializeField] private RectTransform _hpRatingBar;
	[SerializeField] private RectTransform _flameRatingBar;
	[SerializeField] private RectTransform _timeRatingBar;
	[SerializeField] private Text _sessionId;
	
	
//	[SerializeField] private Animator _animator;

	void Awake()
	{
		_sessionId.text = _gameMaster.SessionID.ToString();
	}

	public void show()
	{
		UpdateRatings();
		gameObject.SetActive( true );
//		_animator.enabled = true;
	}

	public void hide()
	{
//		_animator.enabled = false;
		gameObject.SetActive( false );
	}

	public void setScore( string score )
	{
//		var scoreText = transform.Find( "final_score" ) as RectTransform;
//		scoreText.GetComponent< Text >().text = "Final Score: " + score;
	}

	public void SetHealthRating( double hpRemaining, float totalHp )
	{
		float hpPercentage = ( float ) ( hpRemaining / totalHp );
		if ( Math.Abs( hpRemaining ) > 0.0001f ) hpPercentage += 0.15f; //give 10% hp mercy
		_hpRating = ( int ) ( RoundStarRating(
			Mathf.Clamp( hpPercentage, 0f, 1f )  
			* 5) * 2 );
	}

	public void SetFlameRating( int activeFlames, int totalFlames, float averageIntensity, float maxIntensity )
	{
		_flameRating = ( int ) (RoundStarRating( ( 1 - activeFlames / totalFlames ) * 5 ) * 2);
	}

	public void SetTimeRating( double timeRemaining, float totalTime )
	{
		_timeRating = (int) ( RoundStarRating( 
			              Mathf.Clamp( (float) timeRemaining / ( totalTime - 20 ), 0f, 1f ) //give 20 second mercy
		                                       * 5) * 2);
	}

	private float RoundStarRating( float rating )
	{
		int floor = Mathf.FloorToInt( rating );
		int rounded = Mathf.RoundToInt( rating );

		if ( floor == rounded ) return ( int ) rating;
		if ( floor < rounded ) return ( int ) rating + 0.5f;
		throw new Exception("please the humanity");
	}

	private void UpdateRatings()
	{
		Debug.Log( _flameRating );
		Debug.Log( _timeRating );
		Debug.Log( _hpRating );
//		if ( _hpRating == 0 )
//		{
//			_flameRating = 5;
//			_timeRating = 5;
//		} else if ( _timeRating == 0 )
//		{
//			_flameRating /= 2;
//			_hpRating /= 2;
//		}
		_flameRatingBar.sizeDelta = new Vector2( _flameRating * _starWidth / 2, 60 );
		_hpRatingBar.sizeDelta = new Vector2( _hpRating * _starWidth / 2, 60 );
		_timeRatingBar.sizeDelta = new Vector2( _timeRating * _starWidth / 2, 60 );
	}

	public void setMessage( string message )
	{
		if( message == null ) message = "Oh no! You died!";
		var msgText = transform.Find( "message" ) as RectTransform;
//		msgText.GetComponent< Text >().text = message;
	}
}
